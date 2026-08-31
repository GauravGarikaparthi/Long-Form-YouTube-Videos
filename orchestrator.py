from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Optional

from config import load_settings
from models import GeneratedAsset, ScriptPackage, VideoPipelineResult
from api_clients import LLMClient, TTSClient, ImageGenClient, VideoGenClient, AssetManager, RateLimitError, APIError


def setup_logging(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )
    return logging.getLogger("ai_video_pipeline")


class Pipeline:
    def __init__(self, settings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.assets = AssetManager(settings.work_dir, settings.output_dir)
        self.result = VideoPipelineResult(success=False)

    async def run(self, topic: str) -> VideoPipelineResult:
        start = time.time()
        self.logger.info(f"Pipeline started | topic={topic!r} provider={self.settings.llm_provider}")

        try:
            script = await self._stage_expand_script(topic)
            voiceover_path, voice_duration = await self._stage_voiceover(script)
            image_paths = await self._stage_generate_images(script)
            video_segments = await self._stage_animate_images(script, image_paths)
            final_path = await self._stage_assemble(video_segments, voiceover_path, voice_duration, script)

            self.result.success = True
            self.result.video_path = final_path
            self.result.total_duration_seconds = time.time() - start
            self.result.logs.append(f"Pipeline completed successfully in {self.result.total_duration_seconds:.1f}s")
            self.logger.info(f"Pipeline success | output={final_path}")
            return self.result
        except Exception as exc:
            self.result.error = str(exc)
            self.result.logs.append(f"Pipeline failed: {exc}")
            self.logger.error(f"Pipeline failed: {exc}\n{traceback.format_exc()}")
            return self.result

    async def _stage_expand_script(self, topic: str) -> ScriptPackage:
        self.logger.info("Stage 1/5: Expanding script and visual scene breakdown...")
        async with httpx.AsyncClient() as client:
            llm = LLMClient(self.settings, client)
            script = await llm.generate_script(topic, self.settings.target_duration_seconds)
        self.logger.info(f"  -> Title: {script.title} | Sections: {len(script.sections)}")
        for section in script.sections:
            self.assets.log_asset(
                scene_num=section.section_num,
                asset_type="script_section",
                voiceover_text=section.voiceover_text,
                image_prompt=section.image_prompt,
            )
        return script

    async def _stage_voiceover(self, script: ScriptPackage) -> tuple[Path, float]:
        self.logger.info("Stage 2/5: Generating voiceover narration...")
        full_text = "\n\n".join(s.voiceover_text for s in script.sections)
        output_path = self.assets.voiceover_path()
        async with httpx.AsyncClient() as client:
            tts = TTSClient(self.settings, client)
            duration = await tts.synthesize(full_text, output_path)
        self.assets.log_asset(scene_num=0, asset_type="audio", file_path=output_path, duration_seconds=duration)
        self.logger.info(f"  -> Voiceover saved | duration={duration:.1f}s path={output_path}")
        return output_path, duration

    async def _stage_generate_images(self, script: ScriptPackage) -> dict[int, Path]:
        self.logger.info("Stage 3/5: Generating base frames for each scene...")
        image_paths: dict[int, Path] = {}
        async with httpx.AsyncClient() as client:
            img = ImageGenClient(self.settings, client)
            for section in script.sections:
                out = self.assets.scene_image_path(section.section_num)
                self.logger.info(f"  -> Generating image for scene {section.section_num}...")
                try:
                    path = await img.generate_image(section.image_prompt, out)
                    image_paths[section.section_num] = path
                    self.assets.log_asset(scene_num=section.section_num, asset_type="image", file_path=path)
                except RateLimitError as exc:
                    self.logger.warning(f"  Rate limited on scene {section.section_num}, backing off: {exc}")
                    await asyncio.sleep(10)
                    path = await img.generate_image(section.image_prompt, out)
                    image_paths[section.section_num] = path
        return image_paths

    async def _stage_animate_images(self, script: ScriptPackage, image_paths: dict[int, Path]) -> dict[int, Path]:
        self.logger.info("Stage 4/5: Animating images to video segments...")
        video_paths: dict[int, Path] = {}
        async with httpx.AsyncClient() as client:
            vid = VideoGenClient(self.settings, client)
            for section in script.sections:
                img_path = image_paths.get(section.section_num)
                if not img_path:
                    raise APIError(f"Missing image for scene {section.section_num}", provider="pipeline")
                out = self.assets.scene_video_path(section.section_num)
                self.logger.info(f"  -> Animating scene {section.section_num} ({section.animation.duration_seconds}s)...")
                try:
                    path = await vid.generate_video_from_image(img_path, section.image_prompt, out, section.animation)
                    video_paths[section.section_num] = path
                    self.assets.log_asset(
                        scene_num=section.section_num,
                        asset_type="video_segment",
                        file_path=path,
                        duration_seconds=section.animation.duration_seconds,
                    )
                except RateLimitError as exc:
                    self.logger.warning(f"  Rate limited on scene {section.section_num}, backing off: {exc}")
                    await asyncio.sleep(10)
                    path = await vid.generate_video_from_image(img_path, section.image_prompt, out, section.animation)
                    video_paths[section.section_num] = path
        return video_paths

    async def _stage_assemble(
        self, video_segments: dict[int, Path], voiceover_path: Path, voice_duration: float, script: ScriptPackage
    ) -> Path:
        self.logger.info("Stage 5/5: Assembling final video with narration...")
        final_path = self.assets.final_video_path()

        sorted_paths = [video_segments[i] for i in sorted(video_segments)]
        if not sorted_paths:
            raise APIError("No video segments to assemble", provider="pipeline")

        try:
            from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
        except ImportError as exc:
            raise APIError("moviepy is required for video assembly. Install it via requirements.txt.", provider="pipeline") from exc

        clips = []
        for path in sorted_paths:
            clip = VideoFileClip(str(path))
            clips.append(clip)

        combined = concatenate_videoclips(clips, method="compose")
        combined = combined.resize(newsize=self._parse_resolution(self.settings.resolution))

        audio = AudioFileClip(str(voiceover_path))
        if audio.duration > combined.duration:
            audio = audio.subclip(0, combined.duration)

        combined.audio = CompositeAudioClip([audio])
        combined.write_videofile(
            str(final_path),
            fps=self.settings.fps,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger=None,
        )

        for clip in clips:
            clip.close()
        audio.close()
        combined.close()

        self.assets.log_asset(scene_num=0, asset_type="final", file_path=final_path, duration_seconds=combined.duration)
        self.logger.info(f"  -> Final video saved: {final_path}")
        return final_path

    def _parse_resolution(self, resolution: str) -> tuple[int, int]:
        parts = resolution.lower().split("x")
        if len(parts) != 2:
            raise ValueError(f"Invalid resolution format: {resolution}")
        return int(parts[0]), int(parts[1])


def run(topic: str) -> VideoPipelineResult:
    settings = load_settings()
    logger = setup_logging(settings.log_level)
    pipeline = Pipeline(settings, logger)
    return asyncio.run(pipeline.run(topic))


if __name__ == "__main__":
    topic = os.environ.get("TOPIC", "The future of artificial intelligence in healthcare")
    try:
        result = run(topic)
        if result.success:
            print(f"SUCCESS: {result.video_path}")
            sys.exit(0)
        else:
            print(f"FAILED: {result.error}")
            sys.exit(1)
    except Exception as exc:
        print(f"FATAL: {exc}")
        traceback.print_exc()
        sys.exit(1)
