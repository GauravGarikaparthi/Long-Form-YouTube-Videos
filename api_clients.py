from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

import httpx
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import Settings
from models import AnimationParams, ScriptPackage, SceneSection, VideoPipelineResult
from prompts import IMAGE_GEN_PROMPT_TEMPLATE, VIDEO_GEN_PROMPT_TEMPLATE


class APIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, provider: str = "unknown"):
        super().__init__(message)
        self.status_code = status_code
        self.provider = provider


class RateLimitError(APIError):
    pass


def _tenacity_retry():
    return retry(
        retry=retry_if_exception_type((RateLimitError, httpx.TimeoutException, httpx.HTTPStatusError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )


class BaseAPIClient:
    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        self.settings = settings
        self.client = client
        self.timeout = httpx.Timeout(120.0, connect=30.0)


class LLMClient(BaseAPIClient):
    @_tenacity_retry()
    async def generate_script(self, topic: str, target_duration_seconds: float) -> ScriptPackage:
        from prompts import build_script_expansion_user_prompt, SCRIPT_EXPANSION_SYSTEM_PROMPT

        prompt = build_script_expansion_user_prompt(topic, target_duration_seconds)

        if self.settings.llm_provider == "gemini":
            return await self._call_gemini(SCRIPT_EXPANSION_SYSTEM_PROMPT, prompt)
        if self.settings.llm_provider == "claude":
            return await self._call_claude(SCRIPT_EXPANSION_SYSTEM_PROMPT, prompt)
        if self.settings.llm_provider == "groq":
            return await self._call_groq(SCRIPT_EXPANSION_SYSTEM_PROMPT, prompt)
        raise ValueError(f"Unsupported LLM provider: {self.settings.llm_provider}")

    async def _call_gemini(self, system_prompt: str, user_prompt: str) -> ScriptPackage:
        import google.generativeai as genai
        genai.configure(api_key=self.settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-pro", system_instruction=system_prompt)
        response = await asyncio.to_thread(model.generate_content, user_prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(text)
        return ScriptPackage(**data)

    async def _call_claude(self, system_prompt: str, user_prompt: str) -> ScriptPackage:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        message = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = message.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(text)
        return ScriptPackage(**data)

    async def _call_groq(self, system_prompt: str, user_prompt: str) -> ScriptPackage:
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
        }
        resp = await self.client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(text)
        return ScriptPackage(**data)


class TTSClient(BaseAPIClient):
    async def synthesize(self, text: str, output_path: Path) -> float:
        if self.settings.tts_provider == "elevenlabs":
            return await self._elevenlabs(text, output_path)
        if self.settings.tts_provider == "edge_tts":
            return await self._edge_tts(text, output_path)
        raise ValueError(f"Unsupported TTS provider: {self.settings.tts_provider}")

    async def _elevenlabs(self, text: str, output_path: Path) -> float:
        from elevenlabs import ElevenLabs
        client = ElevenLabs(api_key=self.settings.elevenlabs_api_key)
        voice_id = self.settings.elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_turbo_v2_5",
        )
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return self._get_duration(output_path)

    async def _edge_tts(self, text: str, output_path: Path) -> float:
        import edge_tts
        voice = "en-US-GuyNeural"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        return self._get_duration(output_path)

    def _get_duration(self, path: Path) -> float:
        try:
            import soundfile as sf
            with sf.SoundFile(str(path)) as f:
                return len(f) / f.samplerate
        except Exception:
            return 0.0


class ImageGenClient(BaseAPIClient):
    @_tenacity_retry()
    async def generate_image(self, prompt: str, output_path: Path, width: int = 1920, height: int = 1080) -> Path:
        if self.settings.image_gen_provider == "replicate_flux":
            return await self._replicate_flux(prompt, output_path, width, height)
        if self.settings.image_gen_provider == "together_flux":
            return await self._together_flux(prompt, output_path, width, height)
        raise ValueError(f"Unsupported image provider: {self.settings.image_gen_provider}")

    async def _replicate_flux(self, prompt: str, output_path: Path, width: int, height: int) -> Path:
        headers = {
            "Authorization": f"Token {self.settings.replicate_api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "version": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            "input": {"prompt": prompt, "width": width, "height": height, "num_inference_steps": 28},
        }
        resp = await self.client.post("https://api.replicate.com/v1/predictions", json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        prediction = resp.json()
        pred_id = prediction["id"]
        status_url = prediction["urls"]["get"]

        for _ in range(60):
            await asyncio.sleep(3)
            status_resp = await self.client.get(status_url, headers=headers, timeout=self.timeout)
            status_resp.raise_for_status()
            data = status_resp.json()
            if data["status"] == "succeeded":
                url = data["output"]
                img_resp = await self.client.get(url, timeout=self.timeout)
                img_resp.raise_for_status()
                output_path.write_bytes(img_resp.content)
                return output_path
            if data["status"] == "failed":
                raise APIError(f"Replicate image generation failed: {data.get('error')}", provider="replicate")
        raise APIError("Replicate image generation timed out", provider="replicate")

    async def _together_flux(self, prompt: str, output_path: Path, width: int, height: int) -> Path:
        headers = {
            "Authorization": f"Bearer {self.settings.together_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": prompt,
            "width": width,
            "height": height,
            "n": 1,
        }
        resp = await self.client.post(
            "https://api.together.xyz/v1/images/generations",
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        url = data["data"][0]["url"]
        img_resp = await self.client.get(url, timeout=self.timeout)
        img_resp.raise_for_status()
        output_path.write_bytes(img_resp.content)
        return output_path


class VideoGenClient(BaseAPIClient):
    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        super().__init__(settings, client)
        self._video_cache: Dict[str, Path] = {}

    @_tenacity_retry()
    async def generate_video_from_image(
        self,
        image_path: Path,
        prompt: str,
        output_path: Path,
        animation: AnimationParams,
    ) -> Path:
        cache_key = f"{image_path.name}:{prompt}:{animation.duration_seconds}"
        if cache_key in self._video_cache and self._video_cache[cache_key].exists():
            return self._video_cache[cache_key]

        if self.settings.video_gen_provider == "replicate":
            result = await self._replicate_video(image_path, prompt, output_path, animation)
        elif self.settings.video_gen_provider == "together":
            result = await self._together_video(image_path, prompt, output_path, animation)
        elif self.settings.video_gen_provider == "huggingface":
            result = await self._huggingface_video(image_path, prompt, output_path, animation)
        else:
            raise ValueError(f"Unsupported video provider: {self.settings.video_gen_provider}")

        self._video_cache[cache_key] = result
        return result

    async def _replicate_video(
        self, image_path: Path, prompt: str, output_path: Path, animation: AnimationParams
    ) -> Path:
        headers = {
            "Authorization": f"Token {self.settings.replicate_api_token}",
            "Content-Type": "application/json",
        }
        image_url = await self._upload_to_replicate(image_path)
        motion_prompt = VIDEO_GEN_PROMPT_TEMPLATE.substitute(
            scene_description=prompt,
            motion_instruction=animation.camera_movement or "gentle cinematic motion",
        )
        payload = {
            "version": "anotherjesse/zeroscope-v2-xl:9f747673945c62801b13b84701c783929c0ee784e4748ec062204894dda1a351",
            "input": {
                "image": image_url,
                "prompt": motion_prompt,
                "num_frames": int(animation.duration_seconds * animation.fps),
                "fps": animation.fps,
            },
        }
        resp = await self.client.post("https://api.replicate.com/v1/predictions", json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        prediction = resp.json()
        pred_id = prediction["id"]
        status_url = prediction["urls"]["get"]

        for _ in range(120):
            await asyncio.sleep(5)
            status_resp = await self.client.get(status_url, headers=headers, timeout=self.timeout)
            status_resp.raise_for_status()
            data = status_resp.json()
            if data["status"] == "succeeded":
                url = data["output"]
                vid_resp = await self.client.get(url, timeout=self.timeout)
                vid_resp.raise_for_status()
                output_path.write_bytes(vid_resp.content)
                return output_path
            if data["status"] == "failed":
                raise APIError(f"Replicate video generation failed: {data.get('error')}", provider="replicate")
        raise APIError("Replicate video generation timed out", provider="replicate")

    async def _together_video(
        self, image_path: Path, prompt: str, output_path: Path, animation: AnimationParams
    ) -> Path:
        headers = {
            "Authorization": f"Bearer {self.settings.together_api_key}",
            "Content-Type": "application/json",
        }
        motion_prompt = VIDEO_GEN_PROMPT_TEMPLATE.substitute(
            scene_description=prompt,
            motion_instruction=animation.camera_movement or "gentle cinematic motion",
        )
        payload = {
            "model": "tencent/HunyuanVideo",
            "prompt": motion_prompt,
            "input_image": await self._upload_to_together(image_path),
            "duration": min(int(animation.duration_seconds), 10),
        }
        resp = await self.client.post(
            "https://api.together.xyz/v1/videos/generations",
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        generation_id = data.get("id")
        status_url = f"https://api.together.xyz/v1/videos/generations/{generation_id}"

        for _ in range(60):
            await asyncio.sleep(5)
            status_resp = await self.client.get(status_url, headers=headers, timeout=self.timeout)
            status_resp.raise_for_status()
            sdata = status_resp.json()
            if sdata.get("status") == "completed":
                url = sdata["output"]["video_url"]
                vid_resp = await self.client.get(url, timeout=self.timeout)
                vid_resp.raise_for_status()
                output_path.write_bytes(vid_resp.content)
                return output_path
            if sdata.get("status") == "failed":
                raise APIError("Together video generation failed", provider="together")
        raise APIError("Together video generation timed out", provider="together")

    async def _huggingface_video(
        self, image_path: Path, prompt: str, output_path: Path, animation: AnimationParams
    ) -> Path:
        headers = {"Authorization": f"Bearer {self.settings.huggingface_api_key}"}
        motion_prompt = VIDEO_GEN_PROMPT_TEMPLATE.substitute(
            scene_description=prompt,
            motion_instruction=animation.camera_movement or "gentle cinematic motion",
        )
        async with self.client.post(
            "https://api-inference.huggingface.co/models/ByteDance/AnimateDiff-Lightning",
            headers=headers,
            json={"inputs": motion_prompt},
            timeout=self.timeout,
        ) as resp:
            if resp.status_code == 503:
                raise RateLimitError("HuggingFace model loading", provider="huggingface")
            resp.raise_for_status()
            output_path.write_bytes(await resp.read())
            return output_path

    async def _upload_to_replicate(self, image_path: Path) -> str:
        import base64
        with open(image_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        return f"data:application/octet-stream;base64,{content}"

    async def _upload_to_together(self, image_path: Path) -> str:
        import base64
        with open(image_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{content}"


class AssetManager:
    def __init__(self, work_dir: Path, output_dir: Path):
        self.work_dir = work_dir
        self.output_dir = output_dir
        self.assets: list[dict] = []

    def scene_image_path(self, scene_num: int) -> Path:
        return self.work_dir / f"scene_{scene_num:03d}.png"

    def scene_video_path(self, scene_num: int) -> Path:
        return self.work_dir / f"scene_{scene_num:03d}.mp4"

    def voiceover_path(self) -> Path:
        return self.work_dir / "voiceover.wav"

    def final_video_path(self) -> Path:
        return self.output_dir / "final_video.mp4"

    def log_asset(self, **kwargs) -> None:
        self.assets.append(kwargs)
