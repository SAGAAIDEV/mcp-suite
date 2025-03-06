"""Transcriber API Module

This module implements an audio transcription service using AssemblyAI.
It provides functionality to transcribe audio files and return the transcribed text.

Dependencies:
    - assemblyai: For audio transcription
    - dotenv: For environment variable loading
"""

import assemblyai as aai
from dotenv import load_dotenv
from loguru import logger

from src.config.env import ASSEMBLYAI

from ..config.config import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from ..utils.file_utils import get_file_info, validate_audio_file

# Load environment variables from .env file
load_dotenv()


class AssemblyAIService:
    """Service for transcribing audio files using AssemblyAI."""

    def __init__(self):
        """Initialize the transcriber service with API key from environment."""
        api_key = ASSEMBLYAI.API_KEY
        if not api_key:
            raise RuntimeError("ASSEMBLYAI_API_KEY environment variable not set")

        # Initialize AssemblyAI with API key
        aai.settings.api_key = api_key
        logger.info("TranscriberService initialized")

    def transcribe_audio(
        self, audio_path: str, language_code: str = DEFAULT_LANGUAGE
    ) -> str:
        """Transcribe an audio file using AssemblyAI.

        Args:
            audio_path: Path to the audio file
            language_code: Language code for transcription (default: "en")

        Returns:
            Transcribed text from the audio file or error message
        """
        # Validate file
        is_valid, error_message = validate_audio_file(audio_path)
        if not is_valid:
            return error_message

        # Get file info for logging
        file_info = get_file_info(audio_path)

        # Validate language code
        if language_code not in SUPPORTED_LANGUAGES:
            logger.warning(
                f"Unsupported language code: {language_code}. "
                f"Using default: {DEFAULT_LANGUAGE}"
            )
            language_code = DEFAULT_LANGUAGE

        # Create transcription config
        config = aai.TranscriptionConfig(language_code=language_code)
        transcriber = aai.Transcriber(config=config)

        try:
            # Transcribe the file
            logger.info(
                f"Transcribing audio file: {file_info['name']} "
                f"({file_info['size_human']}, "
                f"Language: {SUPPORTED_LANGUAGES[language_code]})"
            )
            transcript = transcriber.transcribe(audio_path)
            return transcript.text

        except Exception as e:
            error_msg = f"Error transcribing file: {str(e)}"
            logger.error(error_msg)
            return error_msg
