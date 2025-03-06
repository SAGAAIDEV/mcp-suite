"""Transcriber Service Configuration

This module contains configuration settings for the transcriber service.
"""

# Supported language codes for transcription
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ru": "Russian",
}

# Default language code
DEFAULT_LANGUAGE = "en"

# Supported audio file formats
SUPPORTED_FORMATS = [
    ".mp3",
    ".mp4",
    ".wav",
    ".ogg",
    ".flac",
    ".m4a",
    ".webm",
]
