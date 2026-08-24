"""
Shared utilities for the viral template system: environment-variable readers
used by template_integration.py, TemplateConfig validation/repair, and the
bridge to background-music selection that assemble_video.py calls directly.
"""

from __future__ import annotations

import os
from dataclasses import replace

from select_music import pick_track
from viral_captions import CAPTION_STYLES
from viral_templates import DEFAULT_TEMPLATE, TemplateConfig

LOG_PREFIX = "[template_utils]"


def log(message: str) -> None:
    print(f"{LOG_PREFIX} {message}", flush=True)


def env_str(name: str, default: str = "") -> str:
    """Read a trimmed environment value, or ``default`` when unset or blank."""
    value = os.environ.get(name, "")
    return value.strip() if value.strip() else default


def env_float(name: str, default: float, lo: float, hi: float) -> float:
    """Read and clamp a numeric environment override without crashing CI."""
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
    """Return human-readable problems with ``config``; an empty list is valid."""
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
    """Repair invalid fields using safe defaults while preserving valid choices."""
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
    """Choose music through the rotation-aware local picker."""
    return pick_track()


__all__ = [
    "log", "env_str", "env_float", "validate_template_config",
    "repair_template_config", "find_music_track",
]
