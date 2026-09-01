"""
Runs the full daily pipeline end to end:
trending topic -> script -> voiceover -> stock clips -> assembled video
-> thumbnail -> packaged metadata artifact (manual upload step).
"""

import json
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from assemble_video import assemble_video
from fetch_visuals import fetch_clips
from generate_illustrations import generate_illustrations
from generate_script import generate_script
from generate_thumbnail import generate_thumbnail
from generate_voiceover import generate_voiceover
from performance_optimizer import media_duration
from select_music import pick_track
from seo_research import research_keywords
from template_integration import apply_template_to_pipeline
from trend_fetch import resolve_topic

WORK_DIR = "work"
OUTPUT_DIR = "output"

# Voiceover uses Kokoro/Piper (local, no API key needed) -- not in this list.
REQUIRED_ENV_VARS = [
    "GROQ_API_KEY",
]


def _check_required_env_vars():
    # Fail fast with one clear message instead of burning steps 1-6 (and
    # their API usage) only to hit a cryptic error on the last step because
    # a GitHub secret was never added or is empty.
    required = list(REQUIRED_ENV_VARS)
    # Illustration mode generates visuals without Pexels, so it must not
    # require a Pexels secret.
    if os.environ.get("VISUAL_STYLE", "pexels").strip().lower() != "illustration":
        required.append("PEXELS_API_KEY")
    missing = [name for name in required if not os.environ.get(name, "").strip()]
    if missing:
        raise RuntimeError(
            "Missing required secret(s): " + ", ".join(missing) + ". "
            "Add them under repo Settings -> Secrets and variables -> Actions "
            "(or export them locally) before running."
        )


def run():
    _check_required_env_vars()
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    topic_mode = os.environ.get("TOPIC_MODE", "trending")
    topic_category = os.environ.get("TOPIC_CATEGORY", "any")
    custom_topic = os.environ.get("CUSTOM_TOPIC", "")
    print(f"Step 1/6: Finding a topic (mode={topic_mode!r}, category={topic_category!r}, custom_topic={custom_topic!r})...")
    if topic_mode == "custom" and not custom_topic.strip():
        print("  WARNING: mode is 'custom' but custom_topic is blank -- falling back to trending.")
    topic = resolve_topic(mode=topic_mode, category=topic_category, custom_topic=custom_topic)
    print(f"  -> Topic: {topic}")

    video_mode = os.environ.get("VIDEO_MODE", "video")
    is_shorts = video_mode == "shorts"

    print("Step 2/6: Researching real search keywords (SEO)...")
    seo_keywords = research_keywords(topic)
    print(f"  -> Keywords: {seo_keywords[:5]}{'...' if len(seo_keywords) > 5 else ''}")

    language = os.environ.get("LANGUAGE", "english")
    print(f"Step 3/6: Generating script + SEO metadata (language={language!r})...")
    package = generate_script(topic, seo_keywords=seo_keywords, language=language)
    print(f"  -> Title: {package['title']}")

    print(f"Step 4/6: Generating voiceover ({language})...")
    voiceover_path = os.path.join(WORK_DIR, "voiceover.wav")
    generate_voiceover(package["narration"], voiceover_path, language=language)

    music_path = pick_track()
    if music_path:
        print(f"  -> Background music: {os.path.basename(music_path)}")

    voice_duration = media_duration(voiceover_path)    
    # VisualProvider: "pexels" | "illustration"
    visual_style = os.environ.get("VISUAL_STYLE", "pexels")
    orientation = "portrait" if is_shorts else "landscape"

    if visual_style == "illustration":
        custom_visual_prompt = os.environ.get("CUSTOM_VISUAL_PROMPT", "").strip()
        if custom_visual_prompt:
            # An exact scene/image prompt drives the VISUALS only -- the
            # narration above is unaffected and keeps coming from the topic,
            # never from this prompt.
            print(f"Step 5/6: Generating AI illustration clips from a custom prompt ({orientation})...")
            illustration_prompts = [custom_visual_prompt] * len(package["visual_keywords"])
        else:
            print(f"Step 5/6: Generating AI illustration clips ({orientation})...")
            illustration_prompts = package["visual_keywords"]
        clip_paths = generate_illustrations(
            illustration_prompts,
            os.path.join(WORK_DIR, "clips"),
            orientation=orientation,
            vary_seed_per_clip=bool(custom_visual_prompt),
        )
    else:  # "pexels" (default)
        print(f"Step 5/6: Fetching stock clips ({orientation})...")
        clip_paths = fetch_clips(
            package["visual_keywords"],
            os.path.join(WORK_DIR, "clips"),
            orientation=orientation,
        )
    if not clip_paths:
        raise RuntimeError("No visual clips generated for any keyword - aborting.")

    template_config = apply_template_to_pipeline(
        topic, num_clips=len(clip_paths), duration=voice_duration,
    )
    print(f"  -> Template: {template_config.name}")
    
    print(f"Step 6/6: Assembling {'Shorts (1080x1920)' if is_shorts else 'video (1920x1080)'} + thumbnail...")
    video_path = os.path.join(OUTPUT_DIR, "video.mp4")
    assemble_video(
        clip_paths, voiceover_path, package["title"], video_path,
        work_dir=WORK_DIR, vertical=is_shorts, narration=package["narration"],
        music_path=music_path, template_config=template_config,
    )
    thumbnail_path = os.path.join(OUTPUT_DIR, "thumbnail.jpg")
    generate_thumbnail(video_path, package["title"], thumbnail_path, _vertical=is_shorts)

    # --- Stage 6: Package final MP4 + AI metadata as a downloadable artifact ---
    # YouTube upload has been removed from this pipeline. The final MP4,
    # thumbnail, and a metadata JSON (title/description/tags/hook) are written
    # to the output/ folder so they can be uploaded as a single GitHub Actions
    # run artifact for manual publishing.
    metadata = {
        "title": package["title"],
        "description": package["description"],
        "tags": package["tags"],
        "hook": package.get("hook", ""),
        "video_path": video_path,
        "thumbnail_path": thumbnail_path,
    }
    metadata_path = os.path.join(OUTPUT_DIR, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Video: {video_path}")
    print(f"  Thumbnail: {thumbnail_path}")
    print(f"  Metadata:  {metadata_path}")
    print("Review the artifacts above and upload manually to YouTube.")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        print("Pipeline failed:")
        traceback.print_exc()
        sys.exit(1)
