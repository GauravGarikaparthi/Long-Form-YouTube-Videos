"""
Assembles the final video from stock clips + voiceover (+ optional background
music) using ffmpeg. Requires ffmpeg and ffprobe to be installed and on PATH.
"""

import math
import os
import re
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_CAPTION_WORDS = 6
XFADE_DURATION = 0.35  # seconds -- short, snappy cuts for fast-paced retention editing
TARGET_FPS = 25  # every clip must share this exactly, or xfade can fail/crash

# Cycled per cut instead of always "fade" -- slideleft/slideright/hblur read as
# quick whip-pan-style swipes, giving cuts more energy and visual variety.
TRANSITIONS = ["fade", "slideleft", "hblur", "slideright", "wiperight", "wipeleft"]

# Clean, bold sans-serif for all on-screen text (captions + title card).
# Downloaded once per CI run into <repo_root>/fonts/ -- see daily_video.yml.
FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", "Montserrat-Bold.ttf"
)
CAPTION_FONT_SIZE = 66
CAPTION_OUTLINE_WIDTH = 7
TITLE_FONT_SIZE = 58

# Background music is ducked well under the voiceover -- it's there for pacing
# and energy, never to compete with narration intelligibility.
MUSIC_VOLUME = 0.10
MUSIC_FADE_SECONDS = 1.5


def _run_ffmpeg(args: list[str]) -> None:
    """
    subprocess.run wrapper that actually prints ffmpeg's stderr when a step
    fails, instead of just the bare command in a CalledProcessError.
    """
    result = subprocess.run(args, capture_output=True)
    if result.returncode != 0:
        stderr_tail = result.stderr.decode(errors="replace")[-4000:]
        print(f"[assemble_video] ffmpeg failed (exit {result.returncode}). Last output:\n{stderr_tail}")
        raise subprocess.CalledProcessError(result.returncode, args, output=result.stdout, stderr=result.stderr)


def _get_duration(path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def _write_caption_file(text: str, path: str) -> str:
    with open(path, "w") as f:
        f.write(text)
    return path


def _chunk_narration_for_captions(narration: str, max_words: int = MAX_CAPTION_WORDS) -> list[dict]:
    """
    Splits narration into short, punchy caption chunks (a handful of words each).
    Returns dicts with word_count alongside text so the caller can time each
    chunk's on-screen duration proportional to how many words it has -- a short
    2-word chunk should flash by much faster than a 6-word one, not sit on
    screen for the same fixed slice, or captions visibly drift out of sync
    with the voiceover well before the video ends.
    """
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", narration.strip()) if s.strip()]

    chunks = []
    for sentence in sentences:
        words = sentence.split()
        for i in range(0, len(words), max_words):
            word_slice = words[i : i + max_words]
            chunk = " ".join(word_slice).strip(".,!?")
            if chunk:
                chunks.append({"text": chunk.upper(), "word_count": len(word_slice)})

    return chunks


def _motion_filter(width: int, height: int, frames: int, fps: int, slot_index: int) -> str:
    """
    Subtle zoom/pan movement for each segment -- gives static-feeling stock
    footage dynamic, parallax/Ken-Burns-style camera motion instead of a flat,
    unmoving shot. Cycles through a few presets so consecutive clips don't all
    move identically.
    """
    presets = [
        ("min(zoom+0.0012,1.15)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        ("if(eq(on,0),1.15,max(zoom-0.0012,1.0))", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        ("1.12", f"iw/2-(iw/zoom/2)+min((iw-iw/zoom)/2,(on/{frames})*(iw*0.12))", "ih/2-(ih/zoom/2)"),
        ("1.12", f"iw/2-(iw/zoom/2)-min((iw-iw/zoom)/2,(on/{frames})*(iw*0.12))", "ih/2-(ih/zoom/2)"),
    ]
    zoom_expr, x_expr, y_expr = presets[slot_index % len(presets)]
    return f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={frames}:s={width}x{height}:fps={fps}"


def _render_segment(job: tuple) -> tuple:
    """
    Renders one looped, motion-cropped segment directly from its source clip
    -- scale/crop/motion/loop all in a single ffmpeg pass, instead of a
    separate "normalize the clip" pass followed by a second "loop it" pass.
    Runs in a worker thread: each call is an independent subprocess, so
    segments for different clips render concurrently rather than one at a
    time, which is the single biggest time cost in the whole pipeline on a
    multi-core CI runner.
    """
    slot_index, clip, seg_path, per_clip_seconds, width, height = job
    frames = max(int(per_clip_seconds * TARGET_FPS), 1)
    motion = _motion_filter(width, height, frames, TARGET_FPS, slot_index)
    _run_ffmpeg(
        [
            "ffmpeg", "-y", "-stream_loop", "-1", "-t", str(per_clip_seconds), "-i", clip,
            "-vf",
            f"scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
            f"crop={width * 2}:{height * 2},{motion}",
            "-r", str(TARGET_FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-threads", "0",
            seg_path,
        ]
    )
    return slot_index, seg_path


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
    - Scales/crops each clip to 1920x1080 (or 1080x1920 for Shorts) with a
      subtle zoom/pan motion, no audio
    - Loops/trims clips to cover the voiceover's total duration, joined with
      varied, fast crossfade-style transitions
    - Adds a simple title card overlay for the first 3 seconds
    - If narration is given, burns in bold, high-contrast-outline captions
      timed proportional to word count
    - Muxes the voiceover as the primary audio track, optionally layering a
      ducked, looped, fade-out background music bed underneath (music_path)
    """
    os.makedirs(work_dir, exist_ok=True)
    voice_duration = _get_duration(voiceover_path)
    width, height = (1080, 1920) if vertical else (1920, 1080)

    if not clip_paths:
        raise ValueError("No clips provided to assemble_video")

    per_clip_seconds = max(voice_duration / len(clip_paths), 3)
    n_slots = math.ceil(voice_duration / per_clip_seconds) + 1

    segment_jobs = [
        (slot, clip_paths[slot % len(clip_paths)], os.path.join(work_dir, f"seg_{slot:02d}.mp4"),
         per_clip_seconds, width, height)
        for slot in range(n_slots)
    ]

    # Segments are independent of each other, so render them concurrently.
    segment_paths = [None] * n_slots
    with ThreadPoolExecutor(max_workers=min(4, os.cpu_count() or 2)) as pool:
        futures = [pool.submit(_render_segment, job) for job in segment_jobs]
        for future in as_completed(futures):
            slot_index, seg_path = future.result()
            segment_paths[slot_index] = seg_path

    concat_video_path = os.path.join(work_dir, "concat_video.mp4")

    if n_slots == 1:
        _run_ffmpeg(
            [
                "ffmpeg", "-y", "-i", segment_paths[0], "-t", str(voice_duration),
                "-c:v", "libx264", "-preset", "veryfast", "-threads", "0",
                concat_video_path,
            ]
        )
    else:
        input_args = []
        for seg_path in segment_paths:
            input_args += ["-i", seg_path]

        filters = []
        prev_label = "0:v"
        cumulative = per_clip_seconds
        for slot in range(1, n_slots):
            offset = cumulative - XFADE_DURATION
            out_label = f"xf{slot}"
            transition = TRANSITIONS[(slot - 1) % len(TRANSITIONS)]
            filters.append(
                f"[{prev_label}][{slot}:v]xfade=transition={transition}:"
                f"duration={XFADE_DURATION}:offset={offset:.3f}[{out_label}]"
            )
            prev_label = out_label
            cumulative += per_clip_seconds - XFADE_DURATION

        _run_ffmpeg(
            [
                "ffmpeg", "-y", *input_args,
                "-filter_complex", ";".join(filters),
                "-map", f"[{prev_label}]",
                "-c:v", "libx264", "-preset", "veryfast", "-threads", "0",
                "-t", str(voice_duration),
                concat_video_path,
            ]
        )

    title_file = _write_caption_file(title_text, os.path.join(work_dir, "title.txt"))
    title_filter = (
        f"drawtext=fontfile='{FONT_PATH}':textfile='{title_file}':"
        f"fontcolor=white:fontsize={TITLE_FONT_SIZE}:"
        "borderw=6:bordercolor=black@0.95:"
        "x=(w-text_w)/2:y=h*0.08:"
        "enable='between(t,0,3.5)'"
    )
    filters = [title_filter]

    if narration:
        caption_start = 3.5
        chunks = _chunk_narration_for_captions(narration)
        remaining = max(voice_duration - caption_start, 0)
        total_words = sum(c["word_count"] for c in chunks) or 1
        if chunks and remaining > 0:
            seconds_per_word = remaining / total_words
            cursor = caption_start
            for i, chunk in enumerate(chunks):
                start = cursor
                end = start + chunk["word_count"] * seconds_per_word
                cursor = end
                caption_file = _write_caption_file(
                    chunk["text"], os.path.join(work_dir, f"caption_{i:02d}.txt")
                )
                filters.append(
                    f"drawtext=fontfile='{FONT_PATH}':textfile='{caption_file}':"
                    f"fontcolor=white:fontsize={CAPTION_FONT_SIZE}:"
                    f"borderw={CAPTION_OUTLINE_WIDTH}:bordercolor=black:"
                    "x=(w-text_w)/2:y=h*0.78:"
                    f"enable='between(t,{start:.2f},{end:.2f})'"
                )

    audio_inputs = ["-i", voiceover_path]
    if music_path:
        audio_inputs += ["-stream_loop", "-1", "-i", music_path]

    if music_path:
        fade_start = max(voice_duration - MUSIC_FADE_SECONDS, 0)
        audio_filter = (
            f"[2:a]volume={MUSIC_VOLUME},afade=t=out:st={fade_start:.2f}:d={MUSIC_FADE_SECONDS}[music];"
            "[1:a][music]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        )
        _run_ffmpeg(
            [
                "ffmpeg", "-y",
                "-i", concat_video_path,
                *audio_inputs,
                "-vf", ",".join(filters),
                "-filter_complex", audio_filter,
                "-map", "0:v:0", "-map", "[aout]",
                "-c:v", "libx264", "-preset", "medium", "-threads", "0",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(voice_duration),
                out_path,
            ]
        )
    else:
        _run_ffmpeg(
            [
                "ffmpeg", "-y",
                "-i", concat_video_path,
                *audio_inputs,
                "-vf", ",".join(filters),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "medium", "-threads", "0",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                out_path,
            ]
        )

    return out_path


if __name__ == "__main__":
    print("Run via main.py with real clip/voiceover paths.")
