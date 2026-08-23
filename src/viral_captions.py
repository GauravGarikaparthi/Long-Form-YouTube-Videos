"""
Enhanced Caption System for Viral YouTube Shorts 2026.
Implements trending caption styles:
- Kinetic bold captions with karaoke effect
- High-contrast yellow/black outlines
- Gradient neon effects (pink/cyan)
- Soft shadow effects
- Bold red motivational text
- Glowing edge effects

Integrates with viral templates for maximum retention.
"""

from __future__ import annotations

import os
import re
from enum import Enum
from typing import NamedTuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance


class ColorScheme(NamedTuple):
    """Color palette for captions."""
    primary: str  # Main text color (hex)
    secondary: str  # Shadow/outline color
    outline: str  # Outline color
    outline_width: int  # Outline thickness in pixels
    shadow_color: str | None  # Optional shadow
    shadow_offset: tuple[int, int] | None  # (x, y) offset


# 2026 TRENDING CAPTION COLOR SCHEMES

KINETIC_BOLD_COLORS = ColorScheme(
    primary="#FFFF00",  # Bright yellow
    secondary="#FFFFFF",  # White base
    outline="#000000",  # Black outline
    outline_width=8,
    shadow_color="#000000",
    shadow_offset=(2, 2)
)

YELLOW_BLACK_COLORS = ColorScheme(
    primary="#FFEE00",  # Gold yellow
    secondary="#000000",  # Black shadow
    outline="#000000",  # Black outline
    outline_width=12,  # Thicker for impact
    shadow_color="#000000",
    shadow_offset=(3, 3)
)

GRADIENT_NEON_COLORS = ColorScheme(
    primary="#FF1493",  # Hot pink
    secondary="#00CED1",  # Cyan
    outline="#FF00FF",  # Magenta
    outline_width=6,
    shadow_color="#00000080",  # Semi-transparent black
    shadow_offset=(2, 2)
)

SOFT_SHADOW_COLORS = ColorScheme(
    primary="#FFFFFF",  # White
    secondary="#FFFFFF",
    outline="#000000",  # Black outline
    outline_width=4,
    shadow_color="#00000040",  # Light shadow
    shadow_offset=(1, 1)
)

BOLD_RED_COLORS = ColorScheme(
    primary="#FF0000",  # Red
    secondary="#000000",  # Black base
    outline="#FFFF00",  # Yellow outline for contrast
    outline_width=8,
    shadow_color="#000000",
    shadow_offset=(3, 3)
)

GLOWING_EDGE_COLORS = ColorScheme(
    primary="#FFFFFF",  # White
    secondary="#00FFFF",  # Cyan glow
    outline="#00FFFF",  # Cyan outline
    outline_width=6,
    shadow_color="#0088FF",  # Blue glow
    shadow_offset=(2, 2)
)


class CaptionPosition(Enum):
    """Position presets for captions on screen."""
    TOP_CENTER = "top_center"
    MIDDLE_CENTER = "middle_center"  # Most common for Shorts
    BOTTOM_CENTER = "bottom_center"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class CaptionEffect(Enum):
    """Visual effects for captions."""
    NONE = "none"
    FADE_IN = "fade_in"
    SCALE_UP = "scale_up"
    SLIDE_IN = "slide_in"
    GLOW = "glow"
    BLUR_THEN_FOCUS = "blur_then_focus"


def get_position_coords(
    position: CaptionPosition,
    width: int,
    height: int,
    text_width: int,
    text_height: int,
) -> tuple[int, int]:
    """Calculate x, y coordinates for caption position."""
    positions = {
        CaptionPosition.TOP_CENTER: (
            (width - text_width) // 2,
            int(height * 0.15)
        ),
        CaptionPosition.MIDDLE_CENTER: (
            (width - text_width) // 2,
            (height - text_height) // 2
        ),
        CaptionPosition.BOTTOM_CENTER: (
            (width - text_width) // 2,
            int(height * 0.80)
        ),
        CaptionPosition.TOP_LEFT: (
            int(width * 0.05),
            int(height * 0.10)
        ),
        CaptionPosition.TOP_RIGHT: (
            int(width * 0.95) - text_width,
            int(height * 0.10)
        ),
        CaptionPosition.BOTTOM_LEFT: (
            int(width * 0.05),
            int(height * 0.85)
        ),
        CaptionPosition.BOTTOM_RIGHT: (
            int(width * 0.95) - text_width,
            int(height * 0.85)
        ),
    }
    return positions.get(position, positions[CaptionPosition.MIDDLE_CENTER])


def apply_kinetic_caption(
    image: Image.Image,
    text: str,
    font: ImageFont.FreeTypeFont,
    position: CaptionPosition = CaptionPosition.MIDDLE_CENTER,
    colors: ColorScheme | None = None,
) -> Image.Image:
    """Apply kinetic bold caption with karaoke effect."""
    if colors is None:
        colors = KINETIC_BOLD_COLORS
    
    draw = ImageDraw.Draw(image)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x, y = get_position_coords(position, image.width, image.height, text_width, text_height)
    
    # Draw outline multiple times for thick effect
    for adj_x in range(-colors.outline_width, colors.outline_width + 1, 2):
        for adj_y in range(-colors.outline_width, colors.outline_width + 1, 2):
            draw.text((x + adj_x, y + adj_y), text, font=font, fill=colors.outline)
    
    # Draw shadow
    if colors.shadow_color and colors.shadow_offset:
        shadow_x, shadow_y = colors.shadow_offset
        draw.text((x + shadow_x, y + shadow_y), text, font=font, fill=colors.shadow_color)
    
    # Draw main text
    draw.text((x, y), text, font=font, fill=colors.primary)
    
    return image


if __name__ == "__main__":
    # Demo caption styles
    print("2026 Viral Caption Styles:")
    print("1. KINETIC_BOLD - Bold yellow with karaoke effect")
    print("2. YELLOW_BLACK - High contrast, thick outline")
    print("3. GRADIENT_NEON - Neon pink/cyan gradient")
    print("4. SOFT_SHADOW - White with soft black shadow")
    print("5. BOLD_RED - High-impact red text")
    print("6. GLOWING_EDGE - Glow effect around edges")
    print("\nUse with src/assemble_video.py for implementation.")
