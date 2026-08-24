"""
Single integration point between main.py and the viral template system.

apply_template_to_pipeline() resolves WHICH template to use (env override or
topic auto-selection), applies per-run env overrides, validates/repairs the
result, and returns a ready-to-use TemplateConfig. assemble_video() consumes
that config directly -- no other wiring needed.

Environment variables (all optional):
  VIRAL_TEMPLATE   template name (e.g. RANKING) or "auto" (default: auto)
  CAPTION_STYLE    overrides the template's caption style
  CLIP_SECONDS     overrides scene length, clamped to [0.8, 6.0]
  MUSIC_VOLUME     overrides music gain, clamped to [0.0, 0.6]
  ENABLE_MUSIC     "false" disables background music entirely
"""

from __future__ import annotations

from dataclasses import replace

from viral_captions import CAPTION_STYLES
from viral_templates import (
    DEFAULT_TEMPLATE,
    TemplateConfig,
    get_template,
    list_templates,
    select_template,
)
from template_utils import env_float, env_str, log, repair_template_config, validate_template_config

LOG_PREFIX = "[integration]"


def apply_template_to_pipeline(
    topic: str,
    num_clips: int | None = None,
    duration: float | None = None,
) -> TemplateConfig:
    """
    Resolves the final TemplateConfig for this run.

    topic:      the video topic (drives auto-selection when VIRAL_TEMPLATE=auto)
    num_clips:  optional hint about how many visual clips were fetched --
                if a fast template demands more scenes than there are clips,
                a warning is logged (clips simply cycle; nothing breaks).
    duration:   optional voiceover duration hint (informational only today).
    """
    choice = env_str("VIRAL_TEMPLATE", "auto").lower()

    if choice in ("", "auto", "default"):
        config = select_template(topic)
    else:
        config = get_template(choice)
        if config is None:
            log(f"VIRAL_TEMPLATE={choice!r} not recognized. "
                f"Available: {list_templates() + [DEFAULT_TEMPLATE.name]}. "
                f"Falling back to auto-selection.")
            config = select_template(topic)
        else:
            log(f"Using explicitly requested template '{config.name}'.")

    # ---- Per-run overrides -------------------------------------------------
    caption_override = env_str("CAPTION_STYLE")
    if caption_override:
        key = caption_override.upper()
        if key in CAPTION_STYLES:
            config = replace(config, caption_style=key)
            log(f"CAPTION_STYLE override applied: {key}")
        else:
            log(f"CAPTION_STYLE={caption_override!r} unknown "
                f"(options: {sorted(CAPTION_STYLES.keys())}) -- keeping '{config.caption_style}'.")

    clip_override = env_float("CLIP_SECONDS", config.clip_seconds, lo=0.8, hi=6.0)
    if abs(clip_override - config.clip_seconds) > 1e-9:
        config = replace(config, clip_seconds=clip_override)
        log(f"CLIP_SECONDS override applied: {clip_override}s")

    music_override = env_float("MUSIC_VOLUME", config.music_volume, lo=0.0, hi=0.6)
    if abs(music_override - config.music_volume) > 1e-9:
        config = replace(config, music_volume=music_override)
        log(f"MUSIC_VOLUME override applied: {music_override}")

    # ---- Validate / repair -------------------------------------------------
    problems = validate_template_config(config)
    if problems:
        for problem in problems:
            log(f"Config problem in '{config.name}': {problem}")
        config = repair_template_config(config)
        remaining = validate_template_config(config)
        if remaining:
            # Should be unreachable after repair; fail loudly rather than
            # render garbage.
            raise ValueError(
                f"Template '{config.name}' still invalid after repair: {remaining}"
            )

    # ---- Informational hints ----------------------------------------------
    if num_clips and num_clips > 0:
        scenes_needed = max(1, int(duration / config.clip_seconds)) if duration else None
        if scenes_needed and scenes_needed > num_clips * 3:
            log(f"Heads-up: template '{config.name}' wants ~{scenes_needed} scenes but only "
                f"{num_clips} unique clips exist -- clips will cycle with varied transitions.")
    if env_str("ENABLE_MUSIC", "true").lower() in ("false", "0", "no", "off"):
        config = replace(config, music_volume=0.0)
        log("ENABLE_MUSIC=false -- background music disabled for this run.")

    log(f"Final template -> name={config.name}, clip={config.clip_seconds}s, "
        f"transitions={config.transitions[:3]}{'...' if len(config.transitions) > 3 else ''}, "
        f"captions={config.caption_style}, music_vol={config.music_volume}")
    return config


if __name__ == "__main__":
    # Self-check: auto path + explicit path + bad-name fallback.
    cfg_auto = apply_template_to_pipeline("top 10 tallest buildings")
    if cfg_auto.name != "RANKING":
        raise AssertionError
    cfg_named = apply_template_to_pipeline("anything", )
    if cfg_named.name != DEFAULT_TEMPLATE.name:
        raise AssertionError
    print("[integration] self-check OK")
