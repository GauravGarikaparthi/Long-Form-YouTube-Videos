"""
Shared utilities for the viral template system: environment-variable readers
used by template_integration.py, TemplateConfig validation/repair, and the
bridge to background-music selection that assemble_video.py calls directly.

This file previously imported names (ViralTemplateType, get_template_config,
select_best_template) that never existed in viral_templates.py, while
template_integration.py imported names FROM here (env_float, env_str, log,
repair_template_config, validate_template_config) that this file never
defined either -- both sides were built against an API that was never
actually implemented. This version matches the real, current
viral_templates.py (TemplateConfig, TEMPLATES, select_template, get_template)
and provides exactly what template_integration.py and assemble_video.py
actually import.
"""

from __future__ import annotations

import os
from dataclasses import replace

from viral_captions import CAPTION_STYLES
from viral_templates import DEFAULT_TEMPLATE, TemplateConfig
from select_music import pick_track

LOG_PREFIX = "[template_utils]"


def log(message: str) -> None:
    print(f"{LOG_PREFIX} {message}", flush=True)


def env_str(name: str, default: str = "") -> str:
    """Reads an environment variable as a stripped string, or `default` if unset/blank."""
    value = os.environ.get(name, "")
    return value.strip() if value.strip() else default


def env_float(name: str, default: float, lo: float, hi: float) -> float:
    """
    Reads an environment variable as a float, clamped to [lo, hi]. Falls back
    to `default` (also clamped) if unset or unparsable -- a malformed
    override should never crash the run.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return max(lo, min(hi, default))
    try:
        value = float(raw)
    except ValueError:
        log(f"{name}={raw!r} is not a valid number -- ignoring override.")
        return max(lo, min(hi, default))
    clamped = max(lo, min(hi, value))
    if clamped != value:
        log(f"{name}={value} out of range [{lo}, {hi}] -- clamped to {clamped}.")
    return clamped


def validate_template_config(config: TemplateConfig) -> list[str]:
    """Returns a list of human-readable problems with a TemplateConfig, empty if valid."""
    problems: list[str] = []

    if config.clip_seconds <= 0:
        problems.append(f"clip_seconds must be positive (got {config.clip_seconds})")
    if config.transition_duration <= 0:
        problems.append(f"transition_duration must be positive (got {config.transition_duration})")
    if config.transition_duration >= config.clip_seconds:
        problems.append(
            f"transition_duration ({config.transition_duration}) must be less than "
            f"clip_seconds ({config.clip_seconds}) or scenes fully overlap"
        )
    if not config.transitions:
        problems.append("transitions palette is empty")
    if not (0.0 <= config.music_volume <= 1.0):
        problems.append(f"music_volume out of [0, 1] range (got {config.music_volume})")
    if config.caption_style.upper() not in CAPTION_STYLES:
        problems.append(f"caption_style '{config.caption_style}' is not a known style")

    return problems


def repair_template_config(config: TemplateConfig) -> TemplateConfig:
    """
    Fixes an invalid TemplateConfig by falling back to DEFAULT_TEMPLATE's
    values field-by-field, only where the current value is actually invalid --
    valid fields on the original config are preserved.
    """
    fixes: dict = {}

    if config.clip_seconds <= 0:
        fixes["clip_seconds"] = DEFAULT_TEMPLATE.clip_seconds
    if config.transition_duration <= 0 or config.transition_duration >= config.clip_seconds:
        fixes["transition_duration"] = min(
            DEFAULT_TEMPLATE.transition_duration,
            fixes.get("clip_seconds", config.clip_seconds) * 0.25,
        )
    if not config.transitions:
        fixes["transitions"] = DEFAULT_TEMPLATE.transitions
    if not (0.0 <= config.music_volume <= 1.0):
        fixes["music_volume"] = DEFAULT_TEMPLATE.music_volume
    if config.caption_style.upper() not in CAPTION_STYLES:
        fixes["caption_style"] = DEFAULT_TEMPLATE.caption_style

    if not fixes:
        return config

    log(f"Repairing template '{config.name}': {list(fixes.keys())}")
    return replace(config, **fixes)


def find_music_track(config: TemplateConfig | None = None) -> str | None:
    """
    Picks a background-music track. Delegates to select_music.pick_track()
    -- the existing rotation-aware picker -- rather than a second
    music-selection system. `config` is accepted for forward compatibility
    (e.g. genre-tagged folders per template later) but isn't used yet.
    """
    return pick_track()


__all__ = [
    "log",
    "env_str",
    "env_float",
    "validate_template_config",
    "repair_template_config",
    "find_music_track",
]
