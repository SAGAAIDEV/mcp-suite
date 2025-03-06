"""Tests for the Transcriber Server MCP Service

This module contains tests for the transcriber server functions.
"""

from unittest.mock import patch

import pytest

from ..config.config import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from ..servers.transcriber_server import transcribe_file, transcriber_service


@pytest.fixture
def mock_transcriber_service():
    """Fixture to mock the transcriber service."""
    # The paths where validate_audio_file is imported and used
    file_validation_paths = [
        "src.mcp_suite.servers.transcriber.utils.file_utils.validate_audio_file",
        "src.mcp_suite.servers.transcriber.service.assemblyai.validate_audio_file",
    ]

    # Setup multiple patches
    patches = [patch(path, return_value=(True, "")) for path in file_validation_paths]

    # Start all patches
    for p in patches:
        p.start()

    # Create a mock for the transcribe_audio method
    with patch.object(
        transcriber_service, "transcribe_audio", autospec=True
    ) as mock_transcribe:
        yield mock_transcribe

    # Stop all patches when test is done
    for p in patches:
        p.stop()


@pytest.mark.asyncio
async def test_transcribe_file_with_default_language(mock_transcriber_service):
    """Test that transcribe_file works with default language."""
    # Arrange
    test_audio_path = "/path/to/audio.mp3"
    expected_text = "This is the transcribed text"
    mock_transcriber_service.return_value = expected_text

    # Act
    result = await transcribe_file(test_audio_path)

    # Assert
    assert result == expected_text
    mock_transcriber_service.assert_called_once_with(test_audio_path, DEFAULT_LANGUAGE)


@pytest.mark.asyncio
async def test_transcribe_file_with_custom_language(mock_transcriber_service):
    """Test that transcribe_file works with a custom language code."""
    # Arrange
    test_audio_path = "/path/to/audio.mp3"
    test_language = "es"  # Spanish
    expected_text = "Este es el texto transcrito"
    mock_transcriber_service.return_value = expected_text

    # Act
    result = await transcribe_file(test_audio_path, test_language)

    # Assert
    assert result == expected_text
    mock_transcriber_service.assert_called_once_with(test_audio_path, test_language)


@pytest.mark.asyncio
async def test_transcribe_file_error_handling(mock_transcriber_service):
    """Test that transcribe_file properly handles error cases."""
    # Arrange
    test_audio_path = "/path/to/nonexistent.mp3"
    error_message = "Error transcribing file: File not found"
    mock_transcriber_service.return_value = error_message

    # Act
    result = await transcribe_file(test_audio_path)

    # Assert
    assert result == error_message
    mock_transcriber_service.assert_called_once_with(test_audio_path, DEFAULT_LANGUAGE)


@pytest.mark.parametrize(
    "language_code",
    list(SUPPORTED_LANGUAGES.keys()),
)
@pytest.mark.asyncio
async def test_transcribe_file_with_supported_languages(
    mock_transcriber_service, language_code
):
    """Test that transcribe_file works with all supported languages."""
    # Arrange
    test_audio_path = "/path/to/audio.mp3"
    expected_text = f"Text in {SUPPORTED_LANGUAGES[language_code]}"
    mock_transcriber_service.return_value = expected_text

    # Act
    result = await transcribe_file(test_audio_path, language_code)

    # Assert
    assert result == expected_text
    mock_transcriber_service.assert_called_once_with(test_audio_path, language_code)


def test_transcriber_service_initialization():
    """Test that the transcriber service initializes correctly."""
    # This test verifies that the service exists
    assert transcriber_service is not None
