from __future__ import annotations

from string import Template

SCRIPT_EXPANSION_SYSTEM_PROMPT = """\
You are an expert video scriptwriter and visual director. Given a topic, produce a structured JSON object that \
represents a complete long-form video plan. The JSON must strictly follow this schema:

{
  "title": "string - catchy, SEO-friendly video title",
  "hook": "string - a single compelling opening line spoken in the first 3 seconds",
  "estimated_total_duration_seconds": 180.0,
  "sections": [
    {
      "section_num": 1,
      "voiceover_text": "string - natural, engaging narration for this section (30-90 words)",
      "image_prompt": "string - detailed cinematic image generation prompt for this section's base frame",
      "animation": {
        "motion_strength": 0.5,
        "fps": 24,
        "duration_seconds": 8.0,
        "easing": "ease-in-out",
        "camera_movement": "slow zoom in"
      },
      "negative_prompt": "string - optional negative prompt to avoid artifacts"
    }
  ]
}

Rules:
- Create 6 to 12 sections depending on the target duration.
- Each voiceover_text must be a complete, spoken-sentence paragraph.
- Image prompts must be vivid, cinematic, and suitable for high-resolution generation.
- animation.duration_seconds per section should sum close to estimated_total_duration_seconds.
- animation.camera_movement should vary across sections for visual interest.
- Return ONLY valid JSON, no markdown fences, no commentary.
"""


def build_script_expansion_user_prompt(topic: str, target_duration_seconds: float) -> str:
    return Template("""\
Topic: $topic
Target total duration: $target_duration seconds

Produce the JSON video plan now.""").substitute(
        topic=topic,
        target_duration=target_duration_seconds,
    )


TTS_NARRATION_PROMPT_TEMPLATE = Template("""\
Please read the following script naturally and clearly at a steady pace. \
Maintain an engaging, informative tone suitable for a documentary-style video:

$script_text""")


IMAGE_GEN_PROMPT_TEMPLATE = Template("""\
Cinematic high-resolution still frame. $scene_description. \
Visual style: photorealistic, 8K, dramatic lighting, shallow depth of field, film grain, anamorphic lens flares. \
No text, no watermarks, no distorted faces.""")


VIDEO_GEN_PROMPT_TEMPLATE = Template("""\
Animate this image into a smooth video clip. $motion_instruction. \
Maintain cinematic quality, 24fps, natural motion, no flicker, no warping.""")
