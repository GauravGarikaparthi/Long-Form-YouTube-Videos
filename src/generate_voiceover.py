"""
Converts narration text into a WAV voiceover using Kokoro (kokoro-onnx) --
an 82M-parameter open-weight local TTS model, run entirely offline via ONNX
Runtime (no PyTorch, no GPU needed). Chosen over Piper for noticeably more
natural prosody at a similar CPU/CI footprint.

Kokoro's shipped voices only cover American/British English, Spanish, French,
Hindi, Italian, Japanese, Brazilian Portuguese, and Mandarin Chinese (see
https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) -- it has no
German, Arabic, Russian, or Turkish voices. Rather than silently drop those
four languages, this falls back to the existing Piper engine for any
language Kokoro doesn't cover (see languages.py).
"""

import os
import subprocess
import sys
import wave

import soundfile as sf
from kokoro_onnx import Kokoro

from _sanitize import sanitize_text
from languages import KOKORO_SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(REPO_ROOT, "models")
KOKORO_MODEL_PATH = os.path.join(MODELS_DIR, "kokoro-v1.0.onnx")
KOKORO_VOICES_PATH = os.path.join(MODELS_DIR, "voices-v1.0.bin")


def _kokoro_available() -> bool:
    return os.path.exists(KOKORO_MODEL_PATH) and os.path.exists(KOKORO_VOICES_PATH)


def _generate_with_kokoro(text: str, out_path: str, voice: str, lang_code: str):
    kokoro = Kokoro(KOKORO_MODEL_PATH, KOKORO_VOICES_PATH)
    samples, sample_rate = kokoro.create(sanitize_text(text), voice=voice, speed=1.0, lang=lang_code)
    sf.write(out_path, samples, sample_rate)


def _generate_with_piper(text: str, out_path: str, voice: str):
    """Fallback path for languages Kokoro doesn't ship voices for."""
    from piper import PiperVoice

    voices_dir = os.path.join(REPO_ROOT, "voices")
    os.makedirs(voices_dir, exist_ok=True)
    model_path = os.path.join(voices_dir, f"{voice}.onnx")
    config_path = model_path + ".json"

    if not (os.path.exists(model_path) and os.path.exists(config_path)):
        print(f"[generate_voiceover] Downloading Piper voice '{voice}' (one-time, ~60MB)...")
        subprocess.run(
            [sys.executable, "-m", "piper.download_voices", voice, "--data-dir", voices_dir],
            check=True,
        )

    tts_voice = PiperVoice.load(model_path)
    with wave.open(out_path, "wb") as wav_file:
        tts_voice.synthesize_wav(sanitize_text(text), wav_file)


def generate_voiceover(text: str, out_path: str, language: str = DEFAULT_LANGUAGE):
    if language in KOKORO_SUPPORTED_LANGUAGES:
        if not _kokoro_available():
            raise RuntimeError(
                f"Kokoro model files not found in {MODELS_DIR}. daily_video.yml should "
                "download kokoro-v1.0.onnx and voices-v1.0.bin before this step runs."
            )
        kokoro_voice, lang_code = KOKORO_SUPPORTED_LANGUAGES[language]
        _generate_with_kokoro(text, out_path, kokoro_voice, lang_code)
    else:
        from languages import voice_for_language
        _generate_with_piper(text, out_path, voice_for_language(language))

    return out_path


if __name__ == "__main__":
    generate_voiceover("This is a test of the automated voiceover pipeline.", "test_voice.wav")
    print("Saved test_voice.wav")
