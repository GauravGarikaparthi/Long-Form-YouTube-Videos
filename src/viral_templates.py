"""
The 10 viral Short templates for 2026 + automatic topic-based selection.

Each template bundles every creative knob the assembler needs:
  - clip_seconds:        target scene length (shorter = higher energy)
  - transition_duration: xfade overlap length between scenes
  - transitions:         palette of xfade effects cycled per junction
  - caption_style:       key into viral_captions.CAPTION_STYLES
  - music_volume:        background music gain (voiceover stays dominant)
  - voice_gain:          voiceover gain before loudness normalization
  - eq:                  color-grade fragment applied to the final video

select_template() scores the topic against each template's keyword list and
picks the best match; ties break on score then definition order. No match ->
DEFAULT_TEMPLATE (a balanced, safe look), so auto-selection can never crash
the pipeline over an unusual topic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

LOG_PREFIX = "[templates]"


def log(message: str) -> None:
    print(f"{LOG_PREFIX} {message}", flush=True)


@dataclass(frozen=True)
class TemplateConfig:
    name: str
    description: str
    clip_seconds: float
    transitions: tuple[str, ...] = ("fade",)
    transition_duration: float = 0.18
    caption_style: str = "KINETIC_BOLD"
    music_volume: float = 0.10
    voice_gain: float = 1.0
    eq: str = ""
    keywords: tuple[str, ...] = field(default_factory=tuple)
    # Explicit scene-length pool (seconds). When set, the assembler cycles
    # these varied durations instead of deriving a pool from clip_seconds --
    # varied cut lengths read as more organic than metronome-regular cuts.
    clip_durations: tuple[float, ...] | None = None


# ---------------------------------------------------------------------------
# The 2026 template set
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, TemplateConfig] = {
    t.name: t
    for t in [
        TemplateConfig(
            name="LOCO",
            description="Ultra-fast music-edit energy (CapCut 'Loco' trend).",
            clip_seconds=1.4,
            transitions=("slideleft", "slideup", "fade", "slideright"),
            transition_duration=0.25,
            caption_style="KINETIC_BOLD",
            music_volume=0.24,
            eq="eq=saturation=1.25:contrast=1.08:brightness=0.02",
            keywords=(
                "loco", "dance", "party", "music", "edit", "hype", "trend",
                "viral dance", "beat drop",
            ),
        ),
        TemplateConfig(
            name="NOSTALGIC_MORPH",
            description="Then-vs-now evolution morphs with warm nostalgic grade.",
            clip_seconds=2.5,
            transitions=("dissolve", "fadeblack", "hblur", "fade"),
            transition_duration=0.5,
            caption_style="SOFT_SHADOW",
            music_volume=0.16,
            eq="eq=saturation=0.92:contrast=0.98:gamma_r=1.04:gamma_b=0.96",
            keywords=(
                "nostalgia", "2016", "evolution", "then vs now", "childhood",
                "memory", "throwback", "years ago", "history", "decade",
                "used to", "growing up",
            ),
        ),
        TemplateConfig(
            name="RANKING",
            description="Top-list / tier-list countdown format.",
            clip_seconds=1.8,
            transitions=("wipeup", "slideleft", "circleopen", "wipedown"),
            transition_duration=0.3,
            caption_style="YELLOW_BLACK",
            music_volume=0.20,
            eq="eq=saturation=1.12:contrast=1.06",
            keywords=(
                "ranking", "ranked", "top", "best", "worst", "tier list",
                "countdown", "list", "number one", "top 5", "top 10",
            ),
        ),
        TemplateConfig(
            name="BEFORE_AFTER",
            description="Satisfying transformation reveals.",
            clip_seconds=2.0,
            transitions=("fadewhite", "circleopen", "dissolve", "radial"),
            transition_duration=0.4,
            caption_style="BOLD_RED",
            music_volume=0.15,
            eq="eq=saturation=1.15:contrast=1.10",
            keywords=(
                "before", "after", "transformation", "glow up", "makeover",
                "renovation", "cleaning", "upgrade", "reveal", "progress",
            ),
        ),
        TemplateConfig(
            name="POV_TRAVELING",
            description="First-person travel/lifestyle flow.",
            clip_seconds=1.6,
            transitions=("smoothleft", "slideup", "fade", "smoothright"),
            transition_duration=0.3,
            caption_style="SOFT_SHADOW",
            music_volume=0.20,
            eq="eq=saturation=1.18:brightness=0.02",
            keywords=(
                "travel", "pov", "city", "beach", "trip", "wanderlust",
                "flight", "hotel", "island", "mountain", "adventure",
                "destination", "tourist",
            ),
        ),
        TemplateConfig(
            name="BEAT_SYNC",
            description="Music-forward cut rhythm for bass-heavy tracks.",
            clip_seconds=2.2,
            transitions=("fade", "fadeblack", "dissolve"),
            transition_duration=0.15,
            caption_style="KINETIC_BOLD",
            music_volume=0.30,
            eq="eq=saturation=1.20:contrast=1.08",
            keywords=(
                "beat", "sync", "bass", "edm", "phonk", "rhythm", "drop",
                "remix", "song", "audio",
            ),
        ),
        TemplateConfig(
            name="GRUNGE_BOLD",
            description="High-contrast grunge look for gaming/fashion edits.",
            clip_seconds=1.5,
            transitions=("pixelize", "distance", "hlslice", "squeezev"),
            transition_duration=0.25,
            caption_style="GLOWING_EDGE",
            music_volume=0.25,
            eq="eq=contrast=1.22:saturation=0.90:gamma=0.96",
            keywords=(
                "grunge", "gaming", "game", "fashion", "streetwear", "skate",
                "punk", "dark aesthetic", "cyber", "neon", "esports",
            ),
        ),
        TemplateConfig(
            name="MOTIVATIONAL_TYPOGRAPHIC",
            description="Bold typographic growth/mindset content.",
            clip_seconds=1.9,
            transitions=("fade", "circleopen", "smoothup", "fadewhite"),
            transition_duration=0.35,
            caption_style="BOLD_RED",
            music_volume=0.18,
            eq="eq=contrast=1.12:saturation=1.05",
            keywords=(
                "motivate", "motivation", "motivational", "discipline",
                "mindset", "grind", "success", "gym", "self improvement",
                "habit", "goal", "productivity", "focus",
            ),
        ),
        TemplateConfig(
            name="BTS",
            description="Behind-the-scenes process footage feel.",
            clip_seconds=2.4,
            transitions=("dissolve", "fade", "smoothleft", "fadeblack"),
            transition_duration=0.45,
            caption_style="YELLOW_BLACK",
            music_volume=0.14,
            eq="eq=saturation=1.02:contrast=1.02",
            keywords=(
                "behind the scenes", "studio", "session", "songwriting",
                "process", "making of", "bts", "recording", "rehearsal",
                "workshop", "backstage",
            ),
        ),
        TemplateConfig(
            name="EVERYDAY_HACKS",
            description="Rapid-fire tips & quick tutorials.",
            clip_seconds=1.3,
            transitions=("slideleft", "wipeup", "circleclose", "slideup"),
            transition_duration=0.2,
            caption_style="KINETIC_BOLD",
            music_volume=0.20,
            eq="eq=saturation=1.15:contrast=1.07:brightness=0.03",
            keywords=(
                "hack", "hacks", "tip", "tips", "tutorial", "how to",
                "diy", "trick", "lifehack", "quick", "easy way", "guide",
            ),
        ),
    ]
}

# Safe fallback used when nothing matches or a config is invalid. Mirrors the
# assembler's previously-tuned neutral look (varied 1.5-2.5s cuts, short
# crossfades, quiet music bed) so passing no template changes nothing.
DEFAULT_TEMPLATE = TemplateConfig(
    name="BALANCED",
    description="Balanced default pacing/look when no template matches.",
    clip_seconds=2.0,
    transitions=("fade", "slideleft", "hblur", "slideright", "wiperight", "wipeleft"),
    transition_duration=0.18,
    caption_style="KINETIC_BOLD",
    music_volume=0.10,
    voice_gain=1.0,
    eq="",
    clip_durations=(1.6, 2.1, 1.8, 2.4, 1.5, 2.5, 1.9, 2.2),
)


def select_template(topic: str) -> TemplateConfig:
    """
    Keyword-scored auto-selection. Counts how many of each template's
    keywords appear in the topic string; highest count wins, ties break by
    definition order (earlier in TEMPLATES = more specific intent).
    """
    topic_lower = (topic or "").lower()
    if not topic_lower.strip():
        log("Empty topic -- using DEFAULT_TEMPLATE.")
        return DEFAULT_TEMPLATE

    best_name: str | None = None
    best_score = 0
    scores: dict[str, int] = {}

    for name, template in TEMPLATES.items():
        score = sum(1 for kw in template.keywords if kw in topic_lower)
        scores[name] = score
        if score > best_score:
            best_score = score
            best_name = name

    if best_name is None or best_score == 0:
        log(f"No keyword match for topic '{topic}' -- using DEFAULT_TEMPLATE.")
        return DEFAULT_TEMPLATE

    chosen = TEMPLATES[best_name]
    matched = [kw for kw in chosen.keywords if kw in topic_lower]
    log(f"Auto-selected template '{chosen.name}' for topic '{topic}' "
        f"(matched keywords: {matched[:4]}).")
    return chosen


def get_template(name: str) -> TemplateConfig | None:
    """Case-insensitive lookup by template name."""
    return TEMPLATES.get((name or "").strip().upper())


def list_templates() -> list[str]:
    return list(TEMPLATES.keys())


if __name__ == "__main__":
    # Self-check: selection sanity across representative topics.
    assert select_template("top 5 space discoveries").name == "RANKING"
    assert select_template("how to fold shirts fast").name == "EVERYDAY_HACKS"
    assert select_template("my 2016 vs now glow up").name == "NOSTALGIC_MORPH"
    assert select_template("quantum flux capacitor repair").name == DEFAULT_TEMPLATE.name
    print(f"[templates] self-check OK ({len(TEMPLATES)} templates)")
