"""
Generates a short narration script + metadata (title, description, tags)
for a faceless YouTube video based on a trending topic.
"""

import os
import json
from groq import Groq

from _sanitize import sanitize_credential
from languages import DEFAULT_LANGUAGE, name_for_language

MODEL = "openai/gpt-oss-120b"


def _language_instruction(language: str) -> str:
    if language == DEFAULT_LANGUAGE:
        return ""
    return (
        f"\n\nWrite your ENTIRE response -- title, description, narration, and tags -- "
        f"in {name_for_language(language)}. Only the JSON keys themselves stay in English."
    )


SYSTEM_PROMPT = """You write scripts for short, faceless narration-style YouTube Shorts \
(30-45 seconds spoken -- short and tight, not a full essay), and you are also an SEO \
copywriter for YouTube.

VOICE: Write like a sharp, friendly expert explaining this to a smart friend over coffee -- \
conversational, a little witty, confident but never condescending. Anticipate the question \
the viewer is silently asking ("wait, why does that even work?", "ok but how do I actually \
do this?") and answer it directly in the next line, as if you read their mind. Avoid \
corporate jargon and buzzwords entirely (no "leverage", "synergy", "unlock your potential", \
"in today's fast-paced world") -- talk like a person, not a LinkedIn post.

HOOK (first sentence, non-negotiable): open with ONE of these proven hook patterns, \
whichever best fits the topic, delivered with a punchy, conversational edge:
- Bold/counterintuitive claim ("Most people get this backwards.")
- Direct question that implies a knowledge gap ("Why do the top 1% do this every morning?")
- Cold open fact/number ("93% of goals fail for one specific reason.")
- Pattern interrupt / myth-bust ("Everything you've heard about X is wrong.")
- Stakes-first ("If you don't fix this by 30, it gets 10x harder.")
Never open with a slow throat-clear like "Have you ever wondered..." or "Let's talk about."

STRUCTURE: hook -> 2-4 tight value/story beats that each earn the next line (cut anything \
that isn't essential, using the "friendly expert" move of naming the question a viewer \
would ask right before answering it) -> a clean ending that lands and ties back to the \
hook (a twist, a payoff, or a direct callback), never trailing off.

SENTENCE LENGTH: keep sentences SHORT (roughly 4-9 words each), one idea per sentence. \
This isn't just style -- narration is auto-split into on-screen caption chunks by sentence, \
so short, self-contained sentences read as clean, well-timed captions instead of being \
awkwardly chopped mid-thought.

Clear simple sentences, no fluff, no stage directions, no headers - just spoken narration \
text. Return ONLY valid JSON, no markdown fences, no preamble."""


def generate_script(
    topic: str,
    seo_keywords: list[str] | None = None,
    api_key: str | None = None,
    language: str = DEFAULT_LANGUAGE,
):
    """
    Returns a dict:
    {
        "title": str,          # YouTube title
        "description": str,    # YouTube description
        "tags": [str, ...],
        "narration": str,      # full voiceover script
        "visual_keywords": [str, ...]  # keywords to search stock footage for
    }

    seo_keywords: real search phrases (e.g. from YouTube autocomplete / Google Trends
    related queries) that the title/description/tags should be built around, instead of
    guessing what people search for.
    """
    client = Groq(api_key=sanitize_credential(api_key or os.environ["GROQ_API_KEY"]))

    keyword_block = ""
    if seo_keywords:
        keyword_list = "\n".join(f"- {kw}" for kw in seo_keywords[:15])
        keyword_block = f"""

Here are REAL phrases people are currently searching for around this topic \
(from YouTube autocomplete and Google Trends related queries) -- use them ONLY as
phrasing hints, never as a replacement for the topic itself:
{keyword_list}

SEO requirements (all secondary to staying on-topic):
- If one of these phrases fits the video's actual content naturally, work it into the
  title early. If none of them genuinely fit -- e.g. they're only loosely related,
  or the topic is niche enough that search data is thin -- ignore this list entirely
  and write a plain, accurate, SEO-reasonable title from the topic alone. Do NOT bend
  the video's subject to match a keyword.
- Same rule for the description and tags: use a phrase only where it's a natural,
  accurate fit for content actually in the narration
- Do NOT keyword-stuff - it must still read naturally to a human"""

    user_prompt = f"""Topic (the video MUST be specifically about this -- do not drift to a \
related but different subject, even if the SEO keywords below point elsewhere): {topic}{keyword_block}

Create a faceless YouTube short-form video package on this exact topic. Respond with ONLY this JSON structure:

{{
  "title": "catchy, SEO-optimized YouTube title, under 70 characters",
  "description": "4-5 sentence SEO-optimized YouTube description, keyword-rich opening, soft call to action to subscribe at the end",
  "tags": ["tag1", "tag2", "..."],
  "narration": "the full 30-45 second spoken script, tight and punchy, first line is a scroll-stopping hook",
  "visual_keywords": ["keyword1", "keyword2", "keyword3", "..."]
}}{_language_instruction(language)}

visual_keywords should always be in English regardless of the response language above -- they're only \
used to search stock footage, never shown to a viewer. They should be 5-8 concrete, filmable nouns/scenes \
(e.g. "ocean waves", "city traffic at night") that match the narration. These keywords are used to search a \
royalty-free STOCK footage library that has no footage of any real, named person, brand, or copyrighted \
movie/show/game -- so NEVER use a person's name, a show/movie/game title, a team name, or a brand as a \
keyword, even if the topic is about a specific person or franchise. Instead describe the generic \
scene/action/mood the narration evokes (e.g. for a video about a footballer, use "soccer player scoring \
goal" or "stadium crowd cheering", not the player's name; for a fantasy show, use "dragon flying over \
castle" or "knights sword fight", not the show's name or any character name)."""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=2048,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    text = response.choices[0].message.content.strip()
    if not text:
        raise RuntimeError(
            "Groq returned an empty response (likely truncated before completing valid "
            "JSON). Try increasing max_tokens further if this recurs."
        )
    # Defensive cleanup in case the model wraps in a code fence anyway
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    return json.loads(text)

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "space discoveries"
    result = generate_script(topic)
    print(json.dumps(result, indent=2))
