"""
Caption styling for viral Shorts -- 6 trending 2026 looks, expressed as
libass (ASS subtitle) style parameters.

WHY ASS: the assembler burns captions through ffmpeg's `subtitles` filter,
which renders word-by-word KARAOKE highlighting -- something drawtext cannot
do. Each style here defines the colors/outline/shadow for that karaoke track,
so switching a template's caption_style restyles every caption in the video.

ALL styles render CENTERED: the assembler pins each caption block with
\\an5 (middle-center alignment) at the exact frame center, inside the
Shorts UI safe zone (clear of the right-side like/description stack and the
bottom ~20%).
"""

from __future__ import annotations

LOG_PREFIX = "[captions]"


def log(message: str) -> None:
    print(f"{LOG_PREFIX} {message}", flush=True)


# ---------------------------------------------------------------------------
# Style definitions
# ---------------------------------------------------------------------------
# primary:      karaoke fill color once a word has been "sung"
# base:         not-yet-sung word color (the karaoke sweep reveals it)
# outline:      outline/border color around glyphs
# outline_ratio outline thickness as a fraction of font size
# shadow:       optional (color, x_offset, y_offset) drop shadow

CAPTION_STYLES: dict[str, dict] = {
    # Bright yellow fill over white base, heavy black outline: the classic
    # high-energy kinetic look.
    "KINETIC_BOLD": {
        "primary": "#FFFF00",
        "base": "#FFFFFF",
        "outline": "#000000",
        "outline_ratio": 0.16,
        "shadow": ("#000000", 2, 2),
    },
    # Gold on black: maximum contrast, reads on any footage.
    "YELLOW_BLACK": {
        "primary": "#FFEE00",
        "base": "#FFAA00",
        "outline": "#000000",
        "outline_ratio": 0.22,
        "shadow": ("#000000", 3, 3),
    },
    # Hot pink fill swept from cyan: neon gradient vibe.
    "GRADIENT_NEON": {
        "primary": "#FF1493",
        "base": "#00CED1",
        "outline": "#1A0033",
        "outline_ratio": 0.12,
        "shadow": ("#FF00FF", 2, 2),
    },
    # Clean white with a soft shadow: minimal vlog style.
    "SOFT_SHADOW": {
        "primary": "#FFFFFF",
        "base": "#E8E8E8",
        "outline": "#000000",
        "outline_ratio": 0.08,
        "shadow": ("#00000040", 1, 1),
    },
    # Red fill swept from yellow: high-impact motivational.
    "BOLD_RED": {
        "primary": "#FF2222",
        "base": "#FFD700",
        "outline": "#000000",
        "outline_ratio": 0.14,
        "shadow": ("#000000", 3, 3),
    },
    # White fill swept from cyan with a blue glow beneath: cyber/gaming.
    "GLOWING_EDGE": {
        "primary": "#FFFFFF",
        "base": "#00FFFF",
        "outline": "#005577",
        "outline_ratio": 0.12,
        "shadow": ("#0088FF", 2, 4),
    },
}

DEFAULT_STYLE = "KINETIC_BOLD"

# Font size as a fraction of frame height (portrait Shorts: ~92px at 1920).
FONT_SIZE_RATIO = 0.048


def get_style(style_key: str) -> dict:
    """Style lookup with safe fallback + warning on unknown keys."""
    style = CAPTION_STYLES.get((style_key or "").strip().upper())
    if style is None:
        log(f"Unknown caption style '{style_key}' -- falling back to {DEFAULT_STYLE}.")
        style = CAPTION_STYLES[DEFAULT_STYLE]
    return style


def hex_to_ass(hex_color: str, alpha: str = "00") -> str:
    """
    Converts '#RRGGBB' to libass '&HAABBGGRR' (note the channel swap and
    leading alpha; '00' alpha = fully opaque).
    """
    raw = hex_color.lstrip("#")
    if len(raw) == 8:  # already carries alpha (#RRGGBBAA)
        alpha, raw = raw[6:8], raw[0:6]
    if len(raw) != 6:
        log(f"Bad color '{hex_color}' -- using white.")
        return "&H00FFFFFF"
    r, g, b = raw[0:2], raw[2:4], raw[4:6]
    return f"&H{alpha.upper()}{b.upper()}{g.upper()}{r.upper()}"


def ass_font_size(height: int) -> int:
    """Caption font size scaled to the render height."""
    return max(28, round(height * FONT_SIZE_RATIO))


def ass_style_line(style_key: str, font_size: int) -> str:
    """
    Builds the ASS '[V4+ Styles]' line for this style. Alignment 5 =
    middle-center; the assembler additionally pins position with \\pos so
    wrapped lines stay centered too.
    """
    style = get_style(style_key)
    outline_px = max(2, round(font_size * style["outline_ratio"]))
    shadow = style.get("shadow")

    # ASS Style fields: BackColour doubles as the shadow colour when
    # BorderStyle=1 and Shadow>0.
    back_colour = hex_to_ass(shadow[0]) if shadow else "&H00000000"
    shadow_depth = max(1, round(font_size * 0.04)) if shadow else 0

    return (
        f"Style: Kinetic,Montserrat,{font_size},"
        f"{hex_to_ass(style['primary'])},"
        f"{hex_to_ass(style['base'])},"
        f"{hex_to_ass(style['outline'])},"
        f"{back_colour},"
        f"-1,0,0,0,100,100,0,0,1,{outline_px},{shadow_depth},5,0,0,0,1"
    )


if __name__ == "__main__":
    # Self-check: color conversion + style-line generation for all styles.
    assert hex_to_ass("#FFFF00") == "&H0000FFFF", hex_to_ass("#FFFF00")
    assert hex_to_ass("#FF1493") == "&H009314FF", hex_to_ass("#FF1493")
    for key in CAPTION_STYLES:
        line = ass_style_line(key, 90)
        assert line.startswith("Style: Kinetic,Montserrat,90,"), line
        assert ",5,0,0,0,1" in line, f"alignment 5 missing for {key}"
    print(f"[captions] self-check OK ({len(CAPTION_STYLES)} styles)")
