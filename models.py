from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    CLAUDE = "claude"
    GROQ = "groq"


class TTSProvider(str, Enum):
    ELEVENLABS = "elevenlabs"
    EDGE_TTS = "edge_tts"


class ImageGenProvider(str, Enum):
    REPLICATE_FLUX = "replicate_flux"
    TOGETHER_FLUX = "together_flux"


class VideoGenProvider(str, Enum):
    REPLICATE = "replicate"
    TOGETHER = "together"
    HUGGINGFACE = "huggingface"


class AnimationParams(BaseModel):
    motion_strength: float = Field(default=0.5, ge=0.0, le=1.0, description="Intensity of camera/object motion")
    fps: int = Field(default=24, ge=12, le=60)
    duration_seconds: float = Field(default=8.0, ge=2.0, le=60.0, description="Target duration for this scene clip")
    easing: str = Field(default="ease-in-out", description="Motion easing curve")
    camera_movement: Optional[str] = Field(default=None, description="e.g., 'slow zoom in', 'pan right'")


class SceneSection(BaseModel):
    section_num: int = Field(ge=1)
    voiceover_text: str = Field(min_length=1)
    image_prompt: str = Field(min_length=1)
    animation: AnimationParams
    negative_prompt: Optional[str] = Field(default=None)


class ScriptPackage(BaseModel):
    title: str = Field(min_length=1)
    hook: str = Field(min_length=1, description="Opening hook line")
    sections: List[SceneSection] = Field(min_length=1)
    estimated_total_duration_seconds: float = Field(ge=10.0)

    @field_validator("sections")
    @classmethod
    def sections_must_be_sequential(cls, v: List[SceneSection]) -> List[SceneSection]:
        nums = [s.section_num for s in v]
        if nums != list(range(1, len(nums) + 1)):
            raise ValueError("Scene sections must be sequentially numbered starting at 1")
        return v


class GeneratedAsset(BaseModel):
    scene_num: int = Field(ge=1)
    asset_type: str = Field(description="image | video_segment | audio | final")
    file_path: Path
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None


class VideoPipelineResult(BaseModel):
    success: bool
    video_path: Optional[Path] = None
    assets: List[GeneratedAsset] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    total_duration_seconds: Optional[float] = None
