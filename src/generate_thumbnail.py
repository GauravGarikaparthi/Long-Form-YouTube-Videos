"""
Generates a 1080x1920 YouTube Shorts thumbnail: a center-cropped video frame
with boosted color and a 3-word ultra-bold teaser in the upper-middle.
Requires ffmpeg for frame extraction. Uses Pillow only (already a dependency).
"""

from __future__ import annotations

import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920

FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", "Montserrat-Bold.ttf"
)

# Prefer heavy display faces when present; Montserrat is bundled in CI.
_FONT_CANDIDATES = (
    FONT_PATH,
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)


def _extract_frame(video_path: str, out_path: str, timestamp: float = 1.5) -> None:
    result = subprocess.run(
        ["ffmpeg", "-y", "-ss", str(timestamp), "-i", video_path, "-frames:v", "1", out_path],
        capture_output=True,
    )
    if result.returncode != 0 or not os.path.isfile(out_path):
        stderr_tail = result.stderr.decode(errors="replace")[-2000:]
        raise RuntimeError(f"Could not extract thumbnail frame from {video_path}: {stderr_tail}")


def _cover_resize(img: Image.Image, width: int, height: int) -> Image.Image:
    """Scale to cover 9:16, then center-crop — never stretch."""
    src_w, src_h = img.size
    if src_w <= 0 or src_h <= 0:
        return img.resize((width, height))
    scale = max(width / src_w, height / src_h)
    new_w = max(int(src_w * scale), width)
    new_h = max(int(src_h * scale), height)
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - width) // 2
    top = (new_h - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _three_word_hook(title_text: str) -> str:
    cleaned = re.sub(r"#shorts\b", "", title_text or "", flags=re.IGNORECASE)
    words = [w.strip(" .,:;!?#\"'") for w in cleaned.split() if w.strip(" .,:;!?#\"'")]
    hook = " ".join(words[:3]).upper()
    return hook or "WATCH THIS"


def _draw_text_with_stroke(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str = "white",
    stroke: str = "black",
    stroke_width: int = 8,
) -> None:
    draw.text(xy, text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke)


def generate_thumbnail(video_path: str, title_text: str, out_path: str, vertical: bool = False):
    """Always emit the official Shorts still size (1080x1920). `vertical` is kept for API compat."""
    width, height = SHORTS_WIDTH, SHORTS_HEIGHT
    frame_path = out_path.replace(".jpg", "_frame.jpg").replace(".png", "_frame.png")
    _extract_frame(video_path, frame_path)

    img = _cover_resize(Image.open(frame_path).convert("RGB"), width, height)
    img = ImageEnhance.Color(img).enhance(1.35)
    img = ImageEnhance.Contrast(img).enhance(1.25)
    img = ImageEnhance.Sharpness(img).enhance(1.15)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    # Soft dark band behind the upper-middle teaser (not the bottom 20% CTA zone).
    band_top = int(height * 0.22)
    band_bottom = int(height * 0.48)
    overlay_draw.rectangle([0, band_top, width, band_bottom], fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    hook = _three_word_hook(title_text)
    words = hook.split()
    font_size = 118 if len(words) <= 3 else 96
    font = _load_font(font_size)
    max_text_width = width - 80

    while font_size > 48:
        widest = max((draw.textlength(w, font=font) for w in words), default=0)
        if widest <= max_text_width:
            break
        font_size -= 6
        font = _load_font(font_size)

    line_height = int(font_size * 1.12)
    block_height = line_height * max(len(words), 1)
    y = int(height * 0.28) - block_height // 2
    y = max(band_top + 16, y)

    for word in words:
        text_w = draw.textlength(word, font=font)
        x = int((width - text_w) / 2)
        _draw_text_with_stroke(draw, (x, y), word, font, fill="#FFEE00", stroke="black", stroke_width=10)
        y += line_height

    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=3))
    img.save(out_path, quality=92, optimize=True)
    return out_path


if __name__ == "__main__":
    print("Run via main.py with a real video path.")
