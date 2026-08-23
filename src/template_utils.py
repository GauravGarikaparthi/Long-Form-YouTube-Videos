"""
Template-aware video assembly enhancements for viral YouTube Shorts 2026.
Extends assemble_video.py with:
- Template-specific clip pacing
- Ranking system overlays
- Polaroid nostalgic frame effects
- Beat synchronization for music
- Transition selection based on template
- High-retention visual hooks
"""

from __future__ import annotations

from typing import Sequence

from viral_templates import (
    ViralTemplateType,
    get_template_config,
)

def get_template_transitions(template_type: ViralTemplateType) -> list[str]:
    """Get optimal transition sequence for a template."""
    config = get_template_config(template_type)
    
    transitions_map = {
        ViralTemplateType.LOCO: [
            "slideleft", "slideright", "fade", "hblur", "wiperight", "wipeleft"
        ],
        ViralTemplateType.NOSTALGIC_MORPH: [
            "xfade", "fade", "fade", "xfade", "fade"
        ],
        ViralTemplateType.RANKING: [
            "slideright", "slideleft", "wiperight", "wipeleft", "fade"
        ],
        ViralTemplateType.BEFORE_AFTER: [
            "fade", "fade", "fade"
        ],
        ViralTemplateType.POV_TRAVELING: [
            "slideleft", "fade", "slideleft", "fade", "slideleft"
        ],
        ViralTemplateType.BEAT_SYNC: [
            "zoomin", "fade", "zoomin", "fade"
        ],
        ViralTemplateType.GRUNGE_BOLD: [
            "wiperight", "wipeleft", "slideleft", "slideright", "hblur"
        ],
        ViralTemplateType.MOTIVATIONAL_TYPOGRAPHIC: [
            "fade", "slideleft", "fade", "wiperight"
        ],
        ViralTemplateType.BTS: [
            "fade", "fade", "fade"
        ],
        ViralTemplateType.EVERYDAY_HACKS: [
            "slideleft", "fade", "slideleft", "slideright", "fade"
        ],
    }
    
    return transitions_map.get(template_type, ["fade", "slideleft"])


def get_template_color_grade(template_type: ViralTemplateType) -> dict:
    """Get color grading adjustments for a template."""
    config = get_template_config(template_type)
    
    color_grading = {
        "vibrant": {
            "saturation": 1.35,
            "brightness": 1.05,
            "contrast": 1.25,
        },
        "warm": {
            "saturation": 1.20,
            "brightness": 1.08,
            "contrast": 1.15,
        },
        "cool": {
            "saturation": 1.15,
            "brightness": 0.95,
            "contrast": 1.20,
        },
        "desaturated": {
            "saturation": 0.70,
            "brightness": 0.90,
            "contrast": 1.40,
        },
    }
    
    return color_grading.get(config.color_grade, color_grading["vibrant"])


def get_music_emphasis_mix(template_type: ViralTemplateType) -> tuple[float, float]:
    """
    Get audio mix levels for a template.
    
    Returns:
        (voice_db, music_db) tuple
    """
    config = get_template_config(template_type)
    
    mixes = {
        "voice_forward": (-3.0, -25.0),  # Voice louder, music quiet
        "music_forward": (-12.0, -15.0),  # Music more prominent
        "balanced": (-6.0, -20.0),  # Balanced mix
    }
    
    return mixes.get(config.audio_emphasis, mixes["balanced"])


def validate_template_compatibility(
    template_type: ViralTemplateType,
    num_clips: int,
    total_duration_seconds: float,
) -> tuple[bool, str]:
    """
    Validate if content is compatible with template.
    
    Returns:
        (is_valid, error_message_or_note)
    """
    config = get_template_config(template_type)
    
    # Check clip count
    if num_clips < 3:
        return False, f"{template_type.value} requires at least 3 clips (you have {num_clips})"
    
    if num_clips > config.max_clips * 2:
        return False, f"{template_type.value} works best with {config.max_clips} or fewer clips"
    
    # Check duration
    min_duration = (config.clip_duration_ms / 1000.0) * 3  # At least 3 clips
    max_duration = 60.0  # YouTube Shorts max
    
    if total_duration_seconds < min_duration:
        return False, f"Content too short for {template_type.value} (min {min_duration}s)"
    
    if total_duration_seconds > max_duration:
        return False, f"Content too long for YouTube Shorts (max 60s, you have {total_duration_seconds}s)"
    
    return True, f"✓ {template_type.value} template is compatible with your content"


# Export for use in main.py
__all__ = [
    "get_template_transitions",
    "get_template_color_grade",
    "get_music_emphasis_mix",
    "validate_template_compatibility",
]
