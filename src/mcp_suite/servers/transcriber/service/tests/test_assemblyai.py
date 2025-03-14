"""
Tests for the AssemblyAI service.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.mcp_suite.servers.transcriber.service.assemblyai import AssemblyAIService


class TestAssemblyAIService:
    """Tests for the AssemblyAIService."""

    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.ASSEMBLYAI")
    def test_init_success(self, mock_assemblyai_config):
        """Test successful initialization of the service."""
        # Setup
        mock_assemblyai_config.API_KEY = "test_api_key"

        # Execute
        with patch("assemblyai.settings") as mock_settings:
            service = AssemblyAIService()

            # Verify
            assert mock_settings.api_key == "test_api_key"

    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.ASSEMBLYAI")
    def test_init_missing_api_key(self, mock_assemblyai_config):
        """Test initialization with missing API key."""
        # Setup
        mock_assemblyai_config.API_KEY = None

        # Execute and verify
        with pytest.raises(RuntimeError, match="ASSEMBLYAI_API_KEY.*not set"):
            AssemblyAIService()

    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.ASSEMBLYAI")
    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.validate_audio_file")
    def test_transcribe_audio_invalid_file(self, mock_validate, mock_assemblyai_config):
        """Test transcribing with an invalid file."""
        # Setup
        mock_assemblyai_config.API_KEY = "test_api_key"
        mock_validate.return_value = (False, "Invalid file error")

        # Execute
        service = AssemblyAIService()
        result = service.transcribe_audio("invalid_file.mp3")

        # Verify
        assert result == "Invalid file error"
        mock_validate.assert_called_once_with("invalid_file.mp3")

    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.ASSEMBLYAI")
    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.validate_audio_file")
    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.get_file_info")
    @patch("assemblyai.Transcriber")
    def test_transcribe_audio_success(
        self, mock_transcriber, mock_get_file_info, mock_validate, mock_assemblyai_config
    ):
        """Test successful audio transcription."""
        # Setup
        mock_assemblyai_config.API_KEY = "test_api_key"
        mock_validate.return_value = (True, "")
        mock_get_file_info.return_value = {
            "name": "test.mp3",
            "size_human": "1.0 MB"
        }

        # Mock the transcriber
        mock_transcript = MagicMock()
        mock_transcript.text = "Transcribed text"
        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = mock_transcript
        mock_transcriber.return_value = mock_transcriber_instance

        # Execute
        service = AssemblyAIService()
        result = service.transcribe_audio("test.mp3")

        # Verify
        assert result == "Transcribed text"
        mock_validate.assert_called_once_with("test.mp3")
        mock_get_file_info.assert_called_once_with("test.mp3")
        mock_transcriber_instance.transcribe.assert_called_once_with("test.mp3")

    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.ASSEMBLYAI")
    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.validate_audio_file")
    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.get_file_info")
    @patch("assemblyai.Transcriber")
    def test_transcribe_audio_unsupported_language(
        self, mock_transcriber, mock_get_file_info, mock_validate, mock_assemblyai_config
    ):
        """Test transcribing with an unsupported language."""
        # Setup
        mock_assemblyai_config.API_KEY = "test_api_key"
        mock_validate.return_value = (True, "")
        mock_get_file_info.return_value = {
            "name": "test.mp3",
            "size_human": "1.0 MB"
        }

        # Mock the transcriber
        mock_transcript = MagicMock()
        mock_transcript.text = "Transcribed text"
        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = mock_transcript
        mock_transcriber.return_value = mock_transcriber_instance

        # Execute
        service = AssemblyAIService()
        result = service.transcribe_audio("test.mp3", language_code="unsupported")

        # Verify
        assert result == "Transcribed text"
        # Should fall back to default language
        mock_transcriber.assert_called_once()
        mock_transcriber_instance.transcribe.assert_called_once_with("test.mp3")

    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.ASSEMBLYAI")
    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.validate_audio_file")
    @patch("src.mcp_suite.servers.transcriber.service.assemblyai.get_file_info")
    @patch("assemblyai.Transcriber")
    def test_transcribe_audio_transcription_error(
        self, mock_transcriber, mock_get_file_info, mock_validate, mock_assemblyai_config
    ):
        """Test error during transcription."""
        # Setup
        mock_assemblyai_config.API_KEY = "test_api_key"
        mock_validate.return_value = (True, "")
        mock_get_file_info.return_value = {
            "name": "test.mp3",
            "size_human": "1.0 MB"
        }

        # Mock the transcriber to raise an exception
        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.side_effect = Exception("Transcription error")
        mock_transcriber.return_value = mock_transcriber_instance

        # Execute
        service = AssemblyAIService()
        result = service.transcribe_audio("test.mp3")

        # Verify
        assert "Error transcribing file" in result
        assert "Transcription error" in result