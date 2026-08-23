"""
Viral 2026 YouTube Shorts Templates Module.
Implements trending template styles including:
- High-emotion transitions (Loco, 2016 vs 2026, Seedance morphing)
- Nostalgic montages with Polaroid styling
- High-retention visual hooks and caption styles
- Before/After transformation effects
- Ranking system templates
"""

from __future__ import annotations

import random
from enum import Enum
from dataclasses import dataclass


class ViralTemplateType(Enum):
    """2026 Trending viral template categories."""
    LOCO = "loco"  # High-energy, fast transitions (2.2M+ uses)
    NOSTALGIC_MORPH = "nostalgic_morph"  # 2016 vs 2026 personal evolution
    RANKING = "ranking"  # Ranked list with progression
    BEFORE_AFTER = "before_after"  # Transformation/satisfaction videos
    POV_TRAVELING = "pov_traveling"  # POV travel/lifestyle content
    BEAT_SYNC = "beat_sync"  # Slow zoom synced to music beats
    GRUNGE_BOLD = "grunge_bold"  # Black/Cyan dynamic grunge aesthetic
    MOTIVATIONAL_TYPOGRAPHIC = "motivational_typographic"  # Bold red/black/yellow text
    BTS = "bts"  # Behind-the-scenes intimate process videos
    EVERYDAY_HACKS = "everyday_hacks"  # Fast-paced informational Q&A


class CaptionStyle(Enum):
    """2026 trending caption styles for high retention."""
    KINETIC_BOLD = "kinetic_bold"  # Bold yellow/white with karaoke effect
    YELLOW_BLACK_OUTLINE = "yellow_black_outline"  # High contrast, thick outline
    GRADIENT_NEON = "gradient_neon"  # Neon pink/cyan gradient
    SOFT_SHADOW = "soft_shadow"  # White with soft black shadow
    BOLD_RED = "bold_red"  # High-impact red text
    GLOWING_EDGE = "glowing_edge"  # Glow effect around edges


class TransitionType(Enum):
    """High-emotion transition effects."""
    FADE = "fade"
    SLIDE_LEFT = "slideleft"
    SLIDE_RIGHT = "slideright"
    ZOOM_IN = "zoomin"
    ZOOM_OUT = "zoomout"
    BLUR_HORIZONTAL = "hblur"
    WIPE_RIGHT = "wiperight"
    WIPE_LEFT = "wipeleft"
    MORPH = "xfade"  # For nostalgic morphing effects


@dataclass
class TemplateConfig:
    """Configuration for a specific viral template."""
    template_type: ViralTemplateType
    caption_style: CaptionStyle
    transition_type: TransitionType
    clip_duration_ms: float  # Duration per clip in milliseconds
    transition_duration_ms: float  # Cross-fade duration
    enable_zoom_pan: bool  # Enable Ken-Burns zoom effect
    enable_music_beat_sync: bool  # Sync visual cuts to music beats
    enable_polaroid_style: bool  # Nostalgic Polaroid frame overlay
    max_clips: int  # Maximum number of clips to use
    color_grade: str  # "warm" | "cool" | "vibrant" | "desaturated"
    audio_emphasis: str  # "voice_forward" | "music_forward" | "balanced"


# PRESET TEMPLATE CONFIGURATIONS FOR 2026 TRENDING STYLES

LOCO_CONFIG = TemplateConfig(
    template_type=ViralTemplateType.LOCO,
    caption_style=CaptionStyle.KINETIC_BOLD,
    transition_type=TransitionType.SLIDE_LEFT,
    clip_duration_ms=1400,  # Fast cuts
    transition_duration_ms=200,
    enable_zoom_pan=True,
    enable_music_beat_sync=True,
    enable_polaroid_style=False,
    max_clips=12,
    color_grade="vibrant",
    audio_emphasis="music_forward"
)

NOSTALGIC_MORPH_CONFIG = TemplateConfig(
    template_type=ViralTemplateType.NOSTALGIC_MORPH,
    caption_style=CaptionStyle.SOFT_SHADOW,
    transition_type=TransitionType.MORPH,
    clip_duration_ms=2500,  # Slower for emotional beats
    transition_duration_ms=800,  # Extended morphing
    enable_zoom_pan=False,
    enable_music_beat_sync=False,
    enable_polaroid_style=True,
    max_clips=6,
    color_grade="warm",
    audio_emphasis="voice_forward"
)

RANKING_CONFIG = TemplateConfig(
    template_type=ViralTemplateType.RANKING,
    caption_style=CaptionStyle.BOLD_RED,
    transition_type=TransitionType.SLIDE_RIGHT,
    clip_duration_ms=1800,
    transition_duration_ms=150,
    enable_zoom_pan=True,
    enable_music_beat_sync=True,
    enable_polaroid_style=False,
    max_clips=8,
    color_grade="vibrant",
    audio_emphasis="balanced"
)

BEFORE_AFTER_CONFIG = TemplateConfig(
    template_type=ViralTemplateType.BEFORE_AFTER,
    caption_style=CaptionStyle.YELLOW_BLACK_OUTLINE,
    transition_type=TransitionType.FADE,
    clip_duration_ms=2000,
    transition_duration_ms=300,
    enable_zoom_pan=False,
    enable_music_beat_sync=False,
    enable_polaroid_style=False,
    max_clips=4,
    color_grade="vibrant",
    audio_emphasis="voice_forward"
)

POV_TRAVELING_CONFIG = TemplateConfig(
    template_type=ViralTemplateType.POV_TRAVELING,
    caption_style=CaptionStyle.SOFT_SHADOW,
    transition_type=TransitionType.SLIDE_LEFT,
    clip_duration_ms=1600,
    transition_duration_ms=180,
    enable_zoom_pan=True,
    enable_music_beat_sync=True,
    enable_polaroid_style=False,
    max_clips=10,
    color_grade="cool",
    audio_emphasis="music_forward"
)

BEAT_SYNC_CONFIG = TemplateConfig(
    template_type=ViralTemplateType.BEAT_SYNC,
    caption_style=CaptionStyle.KINETIC_BOLD,
    transition_type=TransitionType.ZOOM_IN,
    clip_duration_ms=2200,  # Longer, synced to beats
    transition_duration_ms=250,
    enable_zoom_pan=True,
    enable_music_beat_sync=True,
    enable_polaroid_style=False,
    max_clips=8,
    color_grade="vibrant",
    audio_emphasis="music_forward"
)

GRUNGE_BOLD_CONFIG = TemplateConfig(
    template_type=ViralTemplateType.GRUNGE_BOLD,
    caption_style=CaptionStyle.GRADIENT_NEON,
    transition_type=TransitionType.WIPE_RIGHT,
    clip_duration_ms=1500,
    transition_duration_ms=200,
    enable_zoom_pan=True,
    enable_music_beat_sync=True,
    enable_polaroid_style=False,
    max_clips=10,
    color_grade="desaturated",  # Black/Cyan aesthetic
    audio_emphasis="music_forward"
)

MOTIVATIONAL_TYPOGRAPHIC_CONFIG = TemplateConfig(
    template_type=ViralTemplateType.MOTIVATIONAL_TYPOGRAPHIC,
    caption_style=CaptionStyle.BOLD_RED,
    transition_type=TransitionType.FADE,
    clip_duration_ms=1900,
    transition_duration_ms=180,
    enable_zoom_pan=True,
    enable_music_beat_sync=True,
    enable_polaroid_style=False,
    max_clips=8,
    color_grade="vibrant",
    audio_emphasis="music_forward"
)

BTS_CONFIG = TemplateConfig(
    template_type=ViralTemplateType.BTS,
    caption_style=CaptionStyle.SOFT_SHADOW,
    transition_type=TransitionType.FADE,
    clip_duration_ms=2400,  # Longer, intimate pace
    transition_duration_ms=200,
    enable_zoom_pan=False,
    enable_music_beat_sync=False,
    enable_polaroid_style=False,
    max_clips=6,
    color_grade="warm",
    audio_emphasis="voice_forward"
)

EVERYDAY_HACKS_CONFIG = TemplateConfig(
    template_type=ViralTemplateType.EVERYDAY_HACKS,
    caption_style=CaptionStyle.YELLOW_BLACK_OUTLINE,
    transition_type=TransitionType.SLIDE_LEFT,
    clip_duration_ms=1300,  # Fast for rapid Q&A
    transition_duration_ms=150,
    enable_zoom_pan=True,
    enable_music_beat_sync=True,
    enable_polaroid_style=False,
    max_clips=10,
    color_grade="vibrant",
    audio_emphasis="balanced"
)


# Template registry
TEMPLATE_CONFIGS = {
    ViralTemplateType.LOCO: LOCO_CONFIG,
    ViralTemplateType.NOSTALGIC_MORPH: NOSTALGIC_MORPH_CONFIG,
    ViralTemplateType.RANKING: RANKING_CONFIG,
    ViralTemplateType.BEFORE_AFTER: BEFORE_AFTER_CONFIG,
    ViralTemplateType.POV_TRAVELING: POV_TRAVELING_CONFIG,
    ViralTemplateType.BEAT_SYNC: BEAT_SYNC_CONFIG,
    ViralTemplateType.GRUNGE_BOLD: GRUNGE_BOLD_CONFIG,
    ViralTemplateType.MOTIVATIONAL_TYPOGRAPHIC: MOTIVATIONAL_TYPOGRAPHIC_CONFIG,
    ViralTemplateType.BTS: BTS_CONFIG,
    ViralTemplateType.EVERYDAY_HACKS: EVERYDAY_HACKS_CONFIG,
}


def get_template_config(template_type: ViralTemplateType) -> TemplateConfig:
    """Retrieve configuration for a specific template type."""
    return TEMPLATE_CONFIGS[template_type]


def select_best_template(
    topic: str,
    content_category: str | None = None,
) -> tuple[ViralTemplateType, TemplateConfig]:
    """
    Intelligently select the best-performing template for a given topic.
    
    Args:
        topic: The video topic/subject
        content_category: Optional category (e.g., "lifestyle", "educational", "entertainment")
    
    Returns:
        Tuple of (template_type, config)
    """
    topic_lower = topic.lower()
    
    # Content-specific template recommendations
    category_templates = {
        "lifestyle": [ViralTemplateType.POV_TRAVELING, ViralTemplateType.BTS],
        "education": [ViralTemplateType.EVERYDAY_HACKS, ViralTemplateType.MOTIVATIONAL_TYPOGRAPHIC],
        "entertainment": [ViralTemplateType.LOCO, ViralTemplateType.RANKING],
        "transformation": [ViralTemplateType.BEFORE_AFTER, ViralTemplateType.NOSTALGIC_MORPH],
        "process": [ViralTemplateType.BTS, ViralTemplateType.EVERYDAY_HACKS],
        "ranking": [ViralTemplateType.RANKING, ViralTemplateType.MOTIVATIONAL_TYPOGRAPHIC],
        "travel": [ViralTemplateType.POV_TRAVELING, ViralTemplateType.LOCO],
        "music": [ViralTemplateType.BEAT_SYNC, ViralTemplateType.LOCO],
        "aesthetic": [ViralTemplateType.GRUNGE_BOLD, ViralTemplateType.NOSTALGIC_MORPH],
    }
    
    # Topic keyword-based fallback
    keyword_templates = {
        "before": ViralTemplateType.BEFORE_AFTER,
        "after": ViralTemplateType.BEFORE_AFTER,
        "transformation": ViralTemplateType.BEFORE_AFTER,
        "ranking": ViralTemplateType.RANKING,
        "top": ViralTemplateType.RANKING,
        "best": ViralTemplateType.RANKING,
        "worst": ViralTemplateType.RANKING,
        "2016": ViralTemplateType.NOSTALGIC_MORPH,
        "2026": ViralTemplateType.NOSTALGIC_MORPH,
        "evolution": ViralTemplateType.NOSTALGIC_MORPH,
        "journey": ViralTemplateType.NOSTALGIC_MORPH,
        "hack": ViralTemplateType.EVERYDAY_HACKS,
        "tip": ViralTemplateType.EVERYDAY_HACKS,
        "tutorial": ViralTemplateType.EVERYDAY_HACKS,
        "behind": ViralTemplateType.BTS,
        "scenes": ViralTemplateType.BTS,
        "process": ViralTemplateType.BTS,
        "travel": ViralTemplateType.POV_TRAVELING,
        "vlog": ViralTemplateType.POV_TRAVELING,
    }
    
    # Try category-based selection
    if content_category:
        category_lower = content_category.lower()
        if category_lower in category_templates:
            selected = random.choice(category_templates[category_lower])
            return selected, get_template_config(selected)
    
    # Try keyword matching
    for keyword, template_type in keyword_templates.items():
        if keyword in topic_lower:
            return template_type, get_template_config(template_type)
    
    # Default to trending templates with weighted probability
    trending_templates = [
        (ViralTemplateType.LOCO, 0.25),  # Highest usage
        (ViralTemplateType.BEAT_SYNC, 0.20),
        (ViralTemplateType.POV_TRAVELING, 0.15),
        (ViralTemplateType.RANKING, 0.15),
        (ViralTemplateType.NOSTALGIC_MORPH, 0.10),
        (ViralTemplateType.EVERYDAY_HACKS, 0.10),
        (ViralTemplateType.GRUNGE_BOLD, 0.05),
    ]
    
    selected = random.choices(
        [t for t, _ in trending_templates],
        weights=[w for _, w in trending_templates],
        k=1
    )[0]
    
    return selected, get_template_config(selected)


def describe_template(template_type: ViralTemplateType) -> dict:
    """Return human-readable description of a template."""
    descriptions = {
        ViralTemplateType.LOCO: {
            "name": "LOCO (2.2M+ uses)",
            "description": "High-energy viral trend with fast cuts and dynamic transitions.",
            "best_for": "Entertainment, music, high-energy content",
            "retention_hook": "Rapid pacing and constant visual movement",
        },
        ViralTemplateType.NOSTALGIC_MORPH: {
            "name": "2016 vs 2026 Morph",
            "description": "Personal evolution with emotional morphing transitions.",
            "best_for": "Personal development, transformation, nostalgia",
            "retention_hook": "Emotional connection and transformation narrative",
        },
        ViralTemplateType.RANKING: {
            "name": "Ranking System",
            "description": "Structured list with progression and tension building.",
            "best_for": "Top lists, comparisons, educational ranking content",
            "retention_hook": "Curiosity loop and progressive reveals",
        },
        ViralTemplateType.BEFORE_AFTER: {
            "name": "Before & After",
            "description": "Satisfying transformation with visual contrast.",
            "best_for": "Transformations, cleaning, makeovers, results",
            "retention_hook": "Satisfaction and visual transformation proof",
        },
        ViralTemplateType.POV_TRAVELING: {
            "name": "POV Traveling",
            "description": "First-person perspective travel/lifestyle content.",
            "best_for": "Travel, lifestyle, daily vlogs, exploration",
            "retention_hook": "Immersive perspective and discovery",
        },
        ViralTemplateType.BEAT_SYNC: {
            "name": "Slow Zoom & Beat Sync",
            "description": "Visual cuts synchronized to music beats.",
            "best_for": "Music-heavy content, aesthetic, mood-driven",
            "retention_hook": "Rhythmic visual-audio synchronization",
        },
        ViralTemplateType.GRUNGE_BOLD: {
            "name": "Grunge & Bold Aesthetic",
            "description": "High-energy design with black/cyan dynamic grunge.",
            "best_for": "Fashion, gaming, bold advertising, music",
            "retention_hook": "Visual edginess and modern aesthetic",
        },
        ViralTemplateType.MOTIVATIONAL_TYPOGRAPHIC: {
            "name": "Motivational Typographic",
            "description": "Bold red/black/yellow text with motivational messaging.",
            "best_for": "Growth content, motivation, educational, self-improvement",
            "retention_hook": "Powerful text combined with visual storytelling",
        },
        ViralTemplateType.BTS: {
            "name": "Behind-the-Scenes",
            "description": "Intimate process videos showing creation/workflow.",
            "best_for": "Music production, creative process, studio sessions",
            "retention_hook": "Insider perspective and authenticity",
        },
        ViralTemplateType.EVERYDAY_HACKS: {
            "name": "Everyday Hacks & Q&A",
            "description": "Fast-paced informational content with quick tips.",
            "best_for": "Tips, hacks, quick solutions, educational rapid-fire",
            "retention_hook": "Practical value and quick information delivery",
        },
    }
    return descriptions.get(template_type, {})


if __name__ == "__main__":
    import json
    
    # Demo: Show all templates
    for template_type in ViralTemplateType:
        config = get_template_config(template_type)
        desc = describe_template(template_type)
        print(f"\n{desc['name']}")
        print(f"  {desc['description']}")
        print(f"  Best for: {desc['best_for']}")
        print(f"  Clip duration: {config.clip_duration_ms}ms")
        print(f"  Transition: {config.transition_type.value}")
        print(f"  Music sync: {config.enable_music_beat_sync}")
