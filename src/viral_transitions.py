"""
Fast-paced scene transitions for viral Shorts.

The old pipeline hard-coded `xfade=transition=fade` between every scene --
visually flat and a known retention killer. This module cycles through
per-template PALETTES of ffmpeg xfade transitions (slides, wipes, radial
opens, pixelize, blur-dissolve, zoom punches...) so no two consecutive cuts
feel the same.

Every name here is validated against KNOWN_XFADE_TRANSITIONS, a conservative
set that exists in every ffmpeg >= 4.4 build (GitHub Actions runners ship 6/7,
macOS brew ships 7.x). Unknown names are swapped for "fade" with a warning
instead of letting one typo kill an entire render.
"""

from __future__ import annotations

LOG_PREFIX = "[transitions]"


def log(message: str) -> None:
    print(f"{LOG_PREFIX} {message}", flush=True)


# xfade transition names verified against ffmpeg's libavfilter xfade docs.
KNOWN_XFADE_TRANSITIONS = frozenset({
    "fade", "fadeblack", "fadewhite", "fadegrays", "fadefast", "fadeslow",
    "distance",
    "wipeleft", "wiperight", "wipeup", "wipedown",
    "wipetl", "wipetr", "wipebl", "wipebr",
    "slideleft", "slideright", "slideup", "slidedown",
    "circlecrop", "rectcrop", "circleopen", "circleclose",
    "vertopen", "vertclose", "horzopen", "horzclose",
    "radial", "smoothleft", "smoothright", "smoothup", "smoothdown",
    "dissolve", "pixelize", "diagtl", "diagtr", "diagbl", "diagbr",
    "hlslice", "hrslice", "vuslice", "vdslice",
    "hblur", "squeezeh", "squeezev", "zoomin",
})

DEFAULT_TRANSITION = "fade"


def sanitize_palette(palette: tuple[str, ...] | list[str]) -> list[str]:
    """
    Returns a copy of the palette with any unknown/empty transition names
    replaced by DEFAULT_TRANSITION. Logs each substitution so template typos
    surface in CI logs instead of failing mid-render.
    """
    cleaned: list[str] = []
    for name in palette:
        if not name or not isinstance(name, str):
            continue
        if name not in KNOWN_XFADE_TRANSITIONS:
            log(f"Unknown xfade transition '{name}' -- substituting '{DEFAULT_TRANSITION}'.")
            cleaned.append(DEFAULT_TRANSITION)
        else:
            cleaned.append(name)
    if not cleaned:
        cleaned = [DEFAULT_TRANSITION]
    return cleaned


def cycle_transitions(palette: tuple[str, ...] | list[str], count: int) -> list[str]:
    """
    Builds `count` transition names by cycling the palette. A varied palette
    means consecutive junctions get different effects automatically:

        cycle_transitions(("slideleft", "zoomin", "dissolve"), 5)
        -> ["slideleft", "zoomin", "dissolve", "slideleft", "zoomin"]
    """
    if count <= 0:
        return []
    safe = sanitize_palette(palette)
    return [safe[i % len(safe)] for i in range(count)]


def build_xfade_chain(
    segment_count: int,
    per_clip_seconds: float,
    transition_duration: float,
    transitions: list[str],
) -> tuple[list[str], str]:
    """
    Builds the filter_complex fragments that chain N segments together with
    xfade, using a DIFFERENT transition at each junction.

    Returns (filter_lines, final_output_label).

    Offset math: with equal-length segments, junction k happens at
        offset_k = k * (per_clip - transition_duration)
    Each xfade consumes transition_duration seconds of overlap, so the merged
    timeline shrinks accordingly -- callers size the segment count to still
    cover the voiceover after this shrinkage.
    """
    if segment_count < 1:
        raise ValueError("segment_count must be >= 1")

    if segment_count == 1:
        return [], "0:v"

    step = per_clip_seconds - transition_duration
    if step <= 0:
        raise ValueError(
            f"per_clip_seconds ({per_clip_seconds}) must exceed "
            f"transition_duration ({transition_duration}) or scenes fully overlap."
        )

    filters: list[str] = []
    previous_label = "0:v"
    cumulative = per_clip_seconds
    for slot in range(1, segment_count):
        offset = cumulative - transition_duration
        out_label = f"xf{slot}"
        filters.append(
            f"[{previous_label}][{slot}:v]"
            f"xfade=transition={transitions[slot - 1]}:"
            f"duration={transition_duration:.3f}:offset={offset:.3f}"
            f"[{out_label}]"
        )
        previous_label = out_label
        cumulative += step

    return filters, previous_label


if __name__ == "__main__":
    # Self-check: chain building + sanitization round-trip.
    lines, label = build_xfade_chain(
        3, 2.0, 0.35, cycle_transitions(("slideleft", "bogus_fx", "zoomin"), 2)
    )
    assert len(lines) == 2 and label == "xf2"
    assert "transition=slideleft" in lines[0]
    assert "transition=fade" in lines[1], "bogus_fx should have been sanitized to fade"
    print("[transitions] self-check OK")
