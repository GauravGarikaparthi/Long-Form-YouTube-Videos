"""
Assembles the final Shorts-ready video from stock clips + voiceover
(+ optional background music) using ffmpeg.

Requires ffmpeg and ffprobe on PATH. No extra Python video libraries.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# Micro-pacing: visual cuts every 1.5–2.5s (cycled so consecutive shots differ).
CLIP_DURATIONS = (1.6, 2.1, 1.8, 2.4, 1.5, 2.5, 1.9, 2.2)
XFADE_DURATION = 0.18
LOOP_XFADE = 0.40
TARGET_FPS = 25
MAX_SHORTS_SECONDS = 55.0

# Hard 9:16 Shorts canvas. Landscape sources are center-cropped, never stretched.
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920

TRANSITIONS = ["fade", "slideleft", "hblur", "slideright", "wiperight", "wipeleft"]

FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", "Montserrat-Bold.ttf"
)
FONTS_DIR = os.path.dirname(FONT_PATH)

# ASS colours are &HAABBGGRR. Yellow fill, white karaoke base, black outline.
CAPTION_FILL = "&H0000FFFF"
CAPTION_BASE = "&H00FFFFFF"
CAPTION_OUTLINE = "&H00000000"
MAX_CAPTION_WORDS = 3
TITLE_FONT_SIZE = 52

# ~15% linear / -20 dB — present but never competing with Piper TTS.
MUSIC_VOLUME_DB = -20
VOICE_FADE_MS = 0.04


def _run_ffmpeg(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True)
    if result.returncode != 0:
        stderr_tail = result.stderr.decode(errors="replace")[-4000:]
        print(f"[assemble_video] ffmpeg failed (exit {result.returncode}). Last output:\n{stderr_tail}")
        raise subprocess.CalledProcessError(
            result.returncode, args, output=result.stdout, stderr=result.stderr
        )


def _get_duration(path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", path,
        ],
        capture_output=True, text=True, check=True,
    )
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(f"Could not read duration for {path!r}") from exc


def _escape_ffmpeg_path(path: str) -> str:
    return path.replace("\\", "/").replace(":", "\\:").replace("'", r"\'")


def _write_caption_file(text: str, path: str) -> str:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text.replace("\n", " ").strip())
    return path


def _chunk_narration_for_captions(narration: str, max_words: int = MAX_CAPTION_WORDS) -> list[dict]:
    """1–3 word kinetic chunks, timed later from the real voiceover duration."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", narration.strip()) if s.strip()]
    chunks: list[dict] = []
    for sentence in sentences:
        words = [w for w in sentence.split() if w]
        for i in range(0, len(words), max_words):
            word_slice = words[i : i + max_words]
            chunk = " ".join(word_slice).strip(".,!?;:")
            if chunk:
                chunks.append({"text": chunk.upper(), "word_count": len(word_slice)})
    return chunks


def _ass_timestamp(seconds: float) -> str:
    seconds = max(seconds, 0)
    total_cs = int(round(seconds * 100))
    h, rem = divmod(total_cs, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def _ass_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")


def _build_karaoke_ass(
    chunks: list[dict],
    caption_start: float,
    seconds_per_word: float,
    width: int,
    height: int,
    path: str,
) -> str:
    """
    Kinetic captions in the YouTube Shorts UI safe zone:
    middle-third vertically, horizontally centered, extra right margin so
    the like/description stack (right ~10%) and bottom ~20% stay clear.
    """
    font_size = int(height * 0.048)
    # Alignment 5 = middle-center. MarginR ~10% of canvas; MarginV unused for align 5
    # so we pin with \pos to the vertical center of the middle third (y = 50%).
    pos_x = int(width * 0.45)
    pos_y = int(height * 0.50)
    margin_l = int(width * 0.08)
    margin_r = int(width * 0.12)

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {width}\n"
        f"PlayResY: {height}\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Kinetic,Montserrat,{font_size},{CAPTION_FILL},{CAPTION_BASE},"
        f"{CAPTION_OUTLINE},&H00000000,-1,0,0,0,100,100,0,0,1,8,0,5,{margin_l},{margin_r},0,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    lines = [header]
    cursor = caption_start
    for chunk in chunks:
        words = chunk["text"].split()
        if not words:
            continue
        start = cursor
        end = start + len(words) * seconds_per_word
        cursor = end
        kf = max(int(round(seconds_per_word * 100)), 8)
        karaoke = "".join(f"{{\\kf{kf}}}{_ass_escape(w)} " for w in words).strip()
        # \pos keeps the block in the middle third; \fsp adds a bit of tracking.
        text = f"{{\\an5\\pos({pos_x},{pos_y})\\fsp2}}{karaoke}"
        lines.append(
            f"Dialogue: 0,{_ass_timestamp(start)},{_ass_timestamp(end)},Kinetic,,0,0,0,,{text}\n"
        )

    with open(path, "w", encoding="utf-8") as handle:
        handle.writelines(lines)
    return path


def _motion_filter(width: int, height: int, frames: int, fps: int, slot_index: int) -> str:
    """1.1x Ken-Burns zoom/pan so a long Pexels shot still 'resets' the eye."""
    frames = max(frames, 1)
    presets = [
        ("min(zoom+0.0009,1.10)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        ("if(eq(on,0),1.10,max(zoom-0.0009,1.0))", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        ("1.10", f"iw/2-(iw/zoom/2)+min((iw-iw/zoom)/2,(on/{frames})*(iw*0.08))", "ih/2-(ih/zoom/2)"),
        ("1.10", f"iw/2-(iw/zoom/2)-min((iw-iw/zoom)/2,(on/{frames})*(iw*0.08))", "ih/2-(ih/zoom/2)"),
        ("1.08", "iw/2-(iw/zoom/2)", f"ih/2-(ih/zoom/2)+min((ih-ih/zoom)/2,(on/{frames})*(ih*0.06))"),
        ("1.08", "iw/2-(iw/zoom/2)", f"ih/2-(ih/zoom/2)-min((ih-ih/zoom)/2,(on/{frames})*(ih*0.06))"),
    ]
    zoom_expr, x_expr, y_expr = presets[slot_index % len(presets)]
    return (
        f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}'"
        f":d={frames}:s={width}x{height}:fps={fps}"
    )


def _center_crop_chain(width: int, height: int) -> str:
    """
    Scale with aspect preserved until the frame *covers* 9:16, then center-crop.
    Horizontal 16:9 stock becomes a vertical punch-in, never a stretch.
    """
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=increase:force_divisible_by=2,"
        f"crop={width}:{height}"
    )


def _render_segment(job: tuple) -> tuple:
    slot_index, clip, seg_path, per_clip_seconds, width, height = job
    frames = max(int(round(per_clip_seconds * TARGET_FPS)), 1)
    motion = _motion_filter(width, height, frames, TARGET_FPS, slot_index)
    cover = _center_crop_chain(width * 2, height * 2)

    try:
        source_dur = _get_duration(clip)
    except (subprocess.CalledProcessError, RuntimeError):
        source_dur = 0.0

    input_args: list[str]
    if source_dur >= per_clip_seconds + 0.05:
        spare = max(source_dur - per_clip_seconds, 0)
        start = (slot_index * 1.6180339887) % spare if spare > 0 else 0.0
        input_args = ["-ss", f"{start:.3f}", "-t", f"{per_clip_seconds:.3f}", "-i", clip]
    else:
        input_args = ["-stream_loop", "-1", "-t", f"{per_clip_seconds:.3f}", "-i", clip]

    _run_ffmpeg(
        [
            "ffmpeg", "-y", *input_args,
            "-vf", f"{cover},{motion}",
            "-r", str(TARGET_FPS),
            "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-threads", "0",
            seg_path,
        ]
    )
    return slot_index, seg_path


def _plan_slots(voice_duration: float, n_clips: int) -> list[float]:
    """Enough 1.5–2.5s shots to cover the voiceover after xfade shrinkage."""
    durations: list[float] = []
    covered = 0.0
    slot = 0
    while covered < voice_duration + XFADE_DURATION:
        dur = CLIP_DURATIONS[slot % len(CLIP_DURATIONS)]
        durations.append(dur)
        if slot == 0:
            covered = dur
        else:
            covered += dur - XFADE_DURATION
        slot += 1
        if slot > 80:
            break
    if n_clips <= 0:
        raise ValueError("No clips provided to assemble_video")
    return durations


def _concat_with_xfade(segment_paths: list[str], durations: list[float], out_path: str, trim: float) -> None:
    n_slots = len(segment_paths)
    if n_slots == 1:
        _run_ffmpeg(
            [
                "ffmpeg", "-y", "-i", segment_paths[0], "-t", f"{trim:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-an", "-threads", "0",
                out_path,
            ]
        )
        return

    input_args: list[str] = []
    for seg_path in segment_paths:
        input_args += ["-i", seg_path]

    filters: list[str] = []
    prev_label = "0:v"
    cumulative = durations[0]
    for slot in range(1, n_slots):
        offset = max(cumulative - XFADE_DURATION, 0)
        out_label = f"xf{slot}"
        transition = TRANSITIONS[(slot - 1) % len(TRANSITIONS)]
        filters.append(
            f"[{prev_label}][{slot}:v]xfade=transition={transition}:"
            f"duration={XFADE_DURATION}:offset={offset:.3f}[{out_label}]"
        )
        prev_label = out_label
        cumulative += durations[slot] - XFADE_DURATION

    _run_ffmpeg(
        [
            "ffmpeg", "-y", *input_args,
            "-filter_complex", ";".join(filters),
            "-map", f"[{prev_label}]",
            "-c:v", "libx264", "-preset", "veryfast", "-an", "-threads", "0",
            "-t", f"{trim:.3f}",
            out_path,
        ]
    )


def _make_seamless_loop(src: str, dst: str, duration: float) -> None:
    """Crossfade the tail into the head so Shorts auto-replay feels continuous."""
    fade = min(LOOP_XFADE, max(duration * 0.08, 0.15))
    offset = max(duration - fade, 0)
    _run_ffmpeg(
        [
            "ffmpeg", "-y", "-i", src,
            "-filter_complex",
            (
                f"[0:v]split=2[main][head];"
                f"[head]trim=0:{fade:.3f},setpts=PTS-STARTPTS[headc];"
                f"[main][headc]xfade=transition=fade:duration={fade:.3f}:offset={offset:.3f}[vout]"
            ),
            "-map", "[vout]",
            "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-an", "-pix_fmt", "yuv420p", "-threads", "0",
            dst,
        ]
    )


def assemble_video(
    clip_paths: list[str],
    voiceover_path: str,
    title_text: str,
    out_path: str,
    work_dir: str = "work",
    vertical: bool = False,
    narration: str | None = None,
    music_path: str | None = None,
):
    """
    High-retention Shorts assembler:
    - Center-crops every clip to 1080x1920 (9:16) when vertical, else 1920x1080
    - Cuts every 1.5–2.5s with a 1.1x zoom/pan reset
    - Burns 1–3 word kinetic captions in the middle-third safe zone
    - Wraps the last frames into the first for a seamless Shorts loop
    - Mixes Piper TTS over music at -20 dB (~15% linear)
    """
    os.makedirs(work_dir, exist_ok=True)
    if not clip_paths:
        raise ValueError("No clips provided to assemble_video")
    if not os.path.isfile(voiceover_path):
        raise FileNotFoundError(f"Voiceover not found: {voiceover_path}")

    voice_duration = min(_get_duration(voiceover_path), MAX_SHORTS_SECONDS)
    width, height = (SHORTS_WIDTH, SHORTS_HEIGHT) if vertical else (1920, 1080)

    slot_durations = _plan_slots(voice_duration, len(clip_paths))
    n_slots = len(slot_durations)

    segment_jobs = [
        (
            slot,
            clip_paths[slot % len(clip_paths)],
            os.path.join(work_dir, f"seg_{slot:02d}.mp4"),
            slot_durations[slot],
            width,
            height,
        )
        for slot in range(n_slots)
    ]

    segment_paths: list[str | None] = [None] * n_slots
    workers = min(4, os.cpu_count() or 2, n_slots)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_render_segment, job) for job in segment_jobs]
        for future in as_completed(futures):
            slot_index, seg_path = future.result()
            segment_paths[slot_index] = seg_path

    concat_video_path = os.path.join(work_dir, "concat_video.mp4")
    _concat_with_xfade([p for p in segment_paths if p], slot_durations, concat_video_path, voice_duration)

    looped_video_path = os.path.join(work_dir, "looped_video.mp4")
    try:
        _make_seamless_loop(concat_video_path, looped_video_path, voice_duration)
        picture_path = looped_video_path
    except subprocess.CalledProcessError:
        print("[assemble_video] seamless loop pass failed — using linear cut.")
        picture_path = concat_video_path

    vf_parts: list[str] = []
    if os.path.isfile(FONT_PATH):
        title_file = _write_caption_file(title_text, os.path.join(work_dir, "title.txt"))
        vf_parts.append(
            f"drawtext=fontfile='{_escape_ffmpeg_path(FONT_PATH)}':"
            f"textfile='{_escape_ffmpeg_path(title_file)}':"
            f"fontcolor=white:fontsize={TITLE_FONT_SIZE}:"
            "borderw=6:bordercolor=black@0.95:"
            "x=(w-text_w)/2:y=h*0.12:"
            "enable='between(t,0,3)'"
        )

    if narration:
        chunks = _chunk_narration_for_captions(narration)
        remaining = max(voice_duration, 0.01)
        total_words = sum(c["word_count"] for c in chunks) or 1
        if chunks:
            seconds_per_word = remaining / total_words
            ass_path = os.path.join(work_dir, "captions.ass")
            _build_karaoke_ass(chunks, 0.0, seconds_per_word, width, height, ass_path)
            fonts_arg = f":fontsdir={_escape_ffmpeg_path(FONTS_DIR)}" if os.path.isdir(FONTS_DIR) else ""
            vf_parts.append(f"subtitles={_escape_ffmpeg_path(ass_path)}{fonts_arg}")

    fade = min(LOOP_XFADE, max(voice_duration * 0.08, 0.15))
    voice_af = (
        f"afade=t=in:d={VOICE_FADE_MS},afade=t=out:st={max(voice_duration - fade, 0):.3f}:d={fade:.3f}"
    )

    cmd: list[str] = ["ffmpeg", "-y", "-i", picture_path, "-i", voiceover_path]
    filter_complex: str

    if music_path and os.path.isfile(music_path):
        cmd += ["-stream_loop", "-1", "-i", music_path]
        filter_complex = (
            f"[1:a]{voice_af},aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[voice];"
            f"[2:a]volume={MUSIC_VOLUME_DB}dB,"
            f"aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[music];"
            f"[voice][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix];"
            f"[mix]asplit=2[abody][ahead];"
            f"[ahead]atrim=0:{fade:.3f},asetpts=PTS-STARTPTS[ah];"
            f"[abody][ah]acrossfade=d={fade:.3f}:c1=tri:c2=tri[aout]"
        )
        map_audio = "[aout]"
    else:
        filter_complex = (
            f"[1:a]{voice_af},aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[mix];"
            f"[mix]asplit=2[abody][ahead];"
            f"[ahead]atrim=0:{fade:.3f},asetpts=PTS-STARTPTS[ah];"
            f"[abody][ah]acrossfade=d={fade:.3f}:c1=tri:c2=tri[aout]"
        )
        map_audio = "[aout]"

    cmd += ["-filter_complex", filter_complex]
    if vf_parts:
        cmd += ["-vf", ",".join(vf_parts)]
    cmd += [
        "-map", "0:v:0", "-map", map_audio,
        "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p", "-threads", "0",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-t", f"{voice_duration:.3f}",
        "-movflags", "+faststart",
        out_path,
    ]

    try:
        _run_ffmpeg(cmd)
    except subprocess.CalledProcessError:
        # acrossfade can fail on very short VO; mux a simpler mix.
        print("[assemble_video] looped audio mix failed — falling back to linear mix.")
        fallback = ["ffmpeg", "-y", "-i", picture_path, "-i", voiceover_path]
        if music_path and os.path.isfile(music_path):
            fallback += ["-stream_loop", "-1", "-i", music_path]
            fallback += [
                "-filter_complex",
                (
                    f"[1:a]{voice_af}[voice];"
                    f"[2:a]volume={MUSIC_VOLUME_DB}dB[music];"
                    "[voice][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
                ),
            ]
            if vf_parts:
                fallback += ["-vf", ",".join(vf_parts)]
            fallback += ["-map", "0:v:0", "-map", "[aout]"]
        else:
            if vf_parts:
                fallback += ["-vf", ",".join(vf_parts)]
            fallback += ["-map", "0:v:0", "-map", "1:a:0"]
        fallback += [
            "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p", "-threads", "0",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{voice_duration:.3f}",
            "-movflags", "+faststart",
            out_path,
        ]
        _run_ffmpeg(fallback)

    return out_path


if __name__ == "__main__":
    print("Run via main.py with real clip/voiceover paths.")
