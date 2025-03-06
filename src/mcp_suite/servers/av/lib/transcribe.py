from pathlib import Path
from typing import Any, Dict, Union

import assemblyai as aai

from config.env import AssemblyAI

# The API key will be loaded from your .env file through the config
api_key = AssemblyAI().API_KEY

# Initialize the client with your API key
aai.settings.api_key = api_key


def transcribe_media(
    media_path: Union[str, Path],
    language_code: str = "en",
    speaker_labels: bool = False,
    punctuate: bool = True,
    format_text: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """
    Transcribe audio or video file using AssemblyAI.

    Args:
        media_path: Path to the audio or video file
        language_code: Language code (default: "en")
        speaker_labels: Whether to identify different speakers (default: False)
        punctuate: Whether to add punctuation (default: True)
        format_text: Whether to format the text with capitalization (default: True)
        **kwargs: Additional parameters to pass to the transcriber

    Returns:
        Dict containing the transcript and metadata

    Raises:
        FileNotFoundError: If the media file does not exist
        ValueError: If the path is not a file

    Example:
        >>> result = transcribe_media("/path/to/video.mov")
        >>> print(result["text"])
        >>> for utterance in result["utterances"]:
        >>>     print(f"Speaker {utterance.speaker}: {utterance.text}")
    """
    # Convert to Path object for validation
    path_obj = Path(media_path)

    # Check if the file exists
    if not path_obj.exists():
        raise FileNotFoundError(f"Media file not found: {media_path}")

    # Check if it's a file (not a directory)
    if not path_obj.is_file():
        raise ValueError(f"Path is not a file: {media_path}")

    # Convert to string for AssemblyAI
    media_path = str(path_obj)

    # Initialize the transcriber
    transcriber = aai.Transcriber()

    # Configure transcription options
    config = aai.TranscriptionConfig(
        language_code=language_code,
        speaker_labels=speaker_labels,
        punctuate=punctuate,
        format_text=format_text,
        **kwargs,
    )

    # Transcribe the file
    transcript = transcriber.transcribe(media_path, config=config)

    # Return the transcript object which contains various properties
    # like text, utterances, words, etc.
    return transcript
