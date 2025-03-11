"""Transcriber Server MCP Service

This module implements an audio transcription service using AssemblyAI.
It provides functionality to transcribe an audio file and return the transcribed text.

The service is implemented as a FastMCP server that exposes a single tool:
- transcribe_file: Transcribes an audio file and returns its text content

Dependencies:
    - mcp: For FastMCP server implementation
    - transcriber API: For audio transcription functionality

Usage:
    Run this file directly to start the transcriber server:
    ```
    python transcriber_server.py
    ```
"""

from mcp.server.fastmcp import FastMCP

from ..config.config import DEFAULT_LANGUAGE, SUPPORTED_FORMATS, SUPPORTED_LANGUAGES
from ..service.assemblyai import AssemblyAIService

# Initialize the FastMCP server and Transcriber service
mcp = FastMCP("transcriber")
transcriber_service = AssemblyAIService()


@mcp.tool(
    name="transcribe_file",
    description="Transcribe an audio file and return its text content. "
    "Supports multiple audio formats.",
)
async def transcribe_file(audio_path: str, language_code: str = DEFAULT_LANGUAGE) -> str:
    """Transcribe an audio file using AssemblyAI.

    Args:
        audio_path: Path to the audio file
        language_code: Language code for transcription (default: "en")
            Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}

    Returns:
        Transcribed text from the audio file
    """
    return transcriber_service.transcribe_audio(audio_path, language_code)


if __name__ == "__main__":  # pragma: no cover
    # Print service information
    print("Transcriber MCP Service")
    print(
        f"Supported languages: "
        f"{', '.join([f'{code} ({name})' for code, name in SUPPORTED_LANGUAGES.items()])}"
    )
    print(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")

    # Run the MCP server
    mcp.run(transport="stdio")
