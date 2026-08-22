DEFAULT_LANGUAGE = "english"

# Piper fallback voices -- used only for languages Kokoro doesn't ship native
# voices for (see KOKORO_SUPPORTED_LANGUAGES below).
LANGUAGE_VOICES = {
    "english": "en_US-ryan-high",
    "spanish": "es_ES-davefx-medium",
    "french": "fr_FR-siwis-medium",
    "german": "de_DE-thorsten-medium",
    "arabic": "ar_JO-kareem-medium",
    "hindi": "hi_IN-pratham-medium",
    "portuguese": "pt_BR-faber-medium",
    "russian": "ru_RU-irina-medium",
    "turkish": "tr_TR-fettah-medium",
    "chinese": "zh_CN-huayan-medium",
}

# Kokoro (kokoro-onnx) voice id + language code, only for languages it ships
# native voices for. Full catalog:
# https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md -- verify
# there before adding more entries. Languages not listed here fall back to
# Piper via LANGUAGE_VOICES above (German, Arabic, Russian, Turkish as of
# this writing) so they keep working rather than breaking silently.
KOKORO_SUPPORTED_LANGUAGES = {
    "english": ("am_adam", "a"),  # deep, natural male voice, American English
}

LANGUAGE_NAMES = {
    "english": "English",
    "spanish": "Spanish",
    "french": "French",
    "german": "German",
    "arabic": "Arabic",
    "hindi": "Hindi",
    "portuguese": "Portuguese",
    "russian": "Russian",
    "turkish": "Turkish",
    "chinese": "Chinese (Simplified)",
}


def voice_for_language(language: str) -> str:
    """Returns the Piper voice model name for a language key (fallback path only)."""
    return LANGUAGE_VOICES.get(language, LANGUAGE_VOICES[DEFAULT_LANGUAGE])


def name_for_language(language: str) -> str:
    return LANGUAGE_NAMES.get(language, LANGUAGE_NAMES[DEFAULT_LANGUAGE])
