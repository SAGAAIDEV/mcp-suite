"""Tests for the AssemblyAI API module.

This module contains tests for the AssemblyAIService class.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.mcp_suite.servers.transcriber.service.assemblyai import AssemblyAIService


# Mock the AssemblyAI API key
@pytest.fixture
def mock_env():
    with patch(
        "src.mcp_suite.servers.transcriber.service.assemblyai.ASSEMBLYAI"
    ) as mock_env:
        mock_env.API_KEY = "test_api_key"
        yield mock_env


# Mock the AssemblyAI Transcriber
@pytest.fixture
def mock_transcriber():
    with patch("assemblyai.Transcriber") as mock_transcriber_class:
        mock_transcriber_instance = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber_instance

        # Mock the transcribe method
        mock_transcript = MagicMock()
        mock_transcript.text = "This is a test transcription."
        mock_transcriber_instance.transcribe.return_value = mock_transcript

        yield mock_transcriber_instance


# Test file fixture
@pytest.fixture
def test_audio_file():
    # Create a temporary file that looks like an audio file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(b"test audio content")
        temp_path = temp_file.name

    yield temp_path

    # Clean up the temporary file
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestAssemblyAIService:
    """Tests for the AssemblyAIService class."""

    def test_init_missing_api_key(self):
        """Test initialization with missing API key."""
        with patch(
            "src.mcp_suite.servers.transcriber.service.assemblyai.ASSEMBLYAI"
        ) as mock_env:
            mock_env.API_KEY = None

            with pytest.raises(RuntimeError) as excinfo:
                AssemblyAIService()

            assert "ASSEMBLYAI_API_KEY environment variable not set" in str(
                excinfo.value
            )

    def test_transcribe_audio_unsupported_language(
        self, mock_env, mock_transcriber, test_audio_file
    ):
        """Test transcription with an unsupported language code."""
        with patch(
            "src.mcp_suite.servers.transcriber.service.assemblyai.logger"
        ) as mock_logger:
            service = AssemblyAIService()
            result = service.transcribe_audio(
                test_audio_file, "xx"
            )  # Invalid language code

            # Check that a warning was logged
            mock_logger.warning.assert_called_once()
            assert "Unsupported language code" in mock_logger.warning.call_args[0][0]

            # Check that the default language was used
            assert result == "This is a test transcription."

    def test_transcribe_audio_exception(self, mock_env, test_audio_file):
        """Test transcription with an exception during transcription."""
        with patch("assemblyai.Transcriber") as mock_transcriber_class:
            mock_transcriber_instance = MagicMock()
            mock_transcriber_class.return_value = mock_transcriber_instance

            # Mock the transcribe method to raise an exception
            mock_transcriber_instance.transcribe.side_effect = Exception(
                "Test exception"
            )

            with patch(
                "src.mcp_suite.servers.transcriber.service.assemblyai.logger"
            ) as mock_logger:
                service = AssemblyAIService()
                result = service.transcribe_audio(test_audio_file)

                # Check that an error was logged
                mock_logger.error.assert_called_once()

                # Check the result contains the error message
                assert "Error transcribing file" in result
                assert "Test exception" in result
