"""
Integration layer for viral template system into main.py pipeline.
Adds template selection and application to the standard YouTube Shorts workflow.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

# Add src to path (same as main.py does)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from viral_templates import (
    ViralTemplateType,
    select_best_template,
    get_template_config,
    describe_template,
)
from template_utils import (
    get_template_recommendation,
    validate_template_compatibility,
    get_template_color_grade,
    get_music_emphasis_mix,
    should_enable_zoom_pan,
    should_sync_to_music_beats,
    get_template_transitions,
)


def get_template_from_env() -> Optional[ViralTemplateType]:
    """
    Get template preference from environment variable.
    TEMPLATE_TYPE can be: loco, nostalgic_morph, ranking, before_after, pov_traveling,
    beat_sync, grunge_bold, motivational_typographic, bts, everyday_hacks, or 'auto'
    """
    template_env = os.environ.get("TEMPLATE_TYPE", "auto").lower().strip()
    
    if template_env == "auto":
        return None
    
    try:
        return ViralTemplateType(template_env)
    except ValueError:
        print(f"[template_integration] Unknown template type: {template_env}, using auto-selection")
        return None


def select_template_for_content(
    topic: str,
    category: Optional[str] = None,
    force_template: Optional[ViralTemplateType] = None,
) -> tuple[ViralTemplateType, dict]:
    """
    Select and configure template for content.
    
    Args:
        topic: Video topic/subject
        category: Optional content category
        force_template: Force specific template (overrides auto-selection)
    
    Returns:
        (template_type, template_info_dict)
    """
    if force_template:
        template_type = force_template
        config = get_template_config(template_type)
    else:
        template_type, config = select_best_template(topic, category)
    
    description = describe_template(template_type)
    
    template_info = {
        "type": template_type,
        "config": config,
        "name": description.get("name", template_type.value),
        "description": description.get("description", ""),
        "best_for": description.get("best_for", ""),
        "retention_hook": description.get("retention_hook", ""),
        "clip_duration_ms": config.clip_duration_ms,
        "transition_type": config.transition_type.value,
        "enable_zoom_pan": config.enable_zoom_pan,
        "enable_music_beat_sync": config.enable_music_beat_sync,
        "color_grade": get_template_color_grade(template_type),
        "audio_mix": get_music_emphasis_mix(template_type),
    }
    
    return template_type, template_info


def apply_template_to_pipeline(
    topic: str,
    num_clips: int,
    total_duration_seconds: float,
    force_template: Optional[str] = None,
    verbose: bool = True,
) -> dict:
    """
    Full template integration into pipeline.
    
    Args:
        topic: Video topic
        num_clips: Number of available clips
        total_duration_seconds: Total video duration
        force_template: Optional forced template name
        verbose: Print information
    
    Returns:
        Configuration dict for assemble_video
    """
    # Parse forced template
    forced_template_type = None
    if force_template:
        try:
            forced_template_type = ViralTemplateType(force_template.lower())
        except ValueError:
            if verbose:
                print(f"[template_integration] Unknown forced template: {force_template}")
    
    # Select template
    template_type, template_info = select_template_for_content(
        topic,
        category=os.environ.get("CONTENT_CATEGORY"),
        force_template=forced_template_type,
    )
    
    if verbose:
        print(f"\n[template_integration] Selected template: {template_info['name']}")
        print(f"  Description: {template_info['description']}")
        print(f"  Best for: {template_info['best_for']}")
        print(f"  Retention hook: {template_info['retention_hook']}")
    
    # Validate compatibility
    is_valid, validation_msg = validate_template_compatibility(
        template_type, num_clips, total_duration_seconds
    )
    
    if verbose:
        print(f"  Compatibility: {validation_msg}")
    
    if not is_valid:
        if verbose:
            print(f"  ⚠ Warning: {validation_msg}")
    
    # Build assembly configuration
    assembly_config = {
        "template_type": template_type,
        "template_name": template_info["name"],
        "clip_duration": template_info["clip_duration_ms"] / 1000.0,
        "transition": template_info["transition_type"],
        "enable_zoom_pan": template_info["enable_zoom_pan"],
        "enable_music_beat_sync": template_info["enable_music_beat_sync"],
        "color_grade": template_info["color_grade"],
        "audio_voice_db": template_info["audio_mix"][0],
        "audio_music_db": template_info["audio_mix"][1],
        "template_config": template_info["config"],
    }
    
    if verbose:
        print(f"  Clip duration: {assembly_config['clip_duration']}s")
        print(f"  Transitions: {assembly_config['transition']}")
        print(f"  Zoom/Pan: {assembly_config['enable_zoom_pan']}")
        print(f"  Music sync: {assembly_config['enable_music_beat_sync']}")
        print(f"  Color grade: {assembly_config['color_grade']}")
    
    return assembly_config


# Environment variables for template control:
# TEMPLATE_TYPE=<template_name> - Force specific template
# TEMPLATE_AUTO=true (default) - Auto-select template
# TEMPLATE_VERBOSE=true - Print template info
# CONTENT_CATEGORY=<category> - Hint for template selection


if __name__ == "__main__":
    # Test template selection
    test_topics = [
        "Best productivity hacks for 2026",
        "Before and after home renovation",
        "POV traveling through Japan",
        "Top 5 coding mistakes",
        "Behind the scenes music studio session",
        "2016 vs 2026 personal evolution",
    ]
    
    for topic in test_topics:
        print(f"\nTopic: {topic}")
        template_type, info = select_template_for_content(topic)
        print(f"  → {info['name']}")
        print(f"  Clip duration: {info['clip_duration_ms']}ms")
