"""
Tests for the file_utils module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.mcp_suite.servers.transcriber.utils.file_utils import (
    get_file_info,
    get_file_size,
    validate_audio_file,
)


class TestFileUtils:
    """Tests for the file_utils module."""

    @pytest.fixture
    def temp_audio_file(self):
        """Create a temporary audio file for testing."""
        # Create a temporary file with .mp3 extension
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(b"dummy audio content")
            temp_file_path = temp_file.name

        yield temp_file_path

        # Clean up
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    @pytest.fixture
    def invalid_file_path(self):
        """Return a path to a non-existent file."""
        return "/tmp/nonexistent_file.mp3"

    def test_validate_audio_file_success(self, temp_audio_file):
        """Test validating a valid audio file."""
        is_valid, error_msg = validate_audio_file(temp_audio_file)
        assert is_valid is True
        assert error_msg == ""

    def test_validate_audio_file_not_found(self, invalid_file_path):
        """Test validating a non-existent audio file."""
        is_valid, error_msg = validate_audio_file(invalid_file_path)
        assert is_valid is False
        assert "not found" in error_msg.lower()

    def test_validate_audio_file_not_a_file(self, tmp_path):
        """Test validating a directory instead of a file."""
        is_valid, error_msg = validate_audio_file(str(tmp_path))
        assert is_valid is False
        assert "not a file" in error_msg.lower()

    def test_validate_audio_file_unsupported_format(self, tmp_path):
        """Test validating a file with unsupported format."""
        # Create a temporary file with unsupported extension
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("dummy content")

        is_valid, error_msg = validate_audio_file(str(unsupported_file))
        assert is_valid is False
        assert "unsupported audio format" in error_msg.lower()

    @patch("builtins.open")
    def test_validate_audio_file_not_readable(self, mock_open, temp_audio_file):
        """Test validating a file that's not readable."""
        # Mock the open function to raise an exception
        mock_open.side_effect = PermissionError("Permission denied")

        is_valid, error_msg = validate_audio_file(temp_audio_file)
        assert is_valid is False
        assert "not readable" in error_msg.lower()
        assert "permission denied" in error_msg.lower()

    def test_get_file_size_success(self, temp_audio_file):
        """Test getting file size for a valid file."""
        size = get_file_size(temp_audio_file)
        assert size > 0  # We wrote some content to the file

    def test_get_file_size_error(self, invalid_file_path):
        """Test getting file size for a non-existent file."""
        size = get_file_size(invalid_file_path)
        assert size == 0  # Should return 0 for errors

    def test_get_file_info_success(self, temp_audio_file):
        """Test getting file info for a valid file."""
        info = get_file_info(temp_audio_file)

        # Verify basic file info
        assert info["name"] == os.path.basename(temp_audio_file)
        assert info["path"] == str(Path(temp_audio_file).absolute())
        assert info["size"] > 0
        assert info["extension"] == ".mp3"
        assert info["exists"] is True
        assert info["is_file"] is True
        assert "size_human" in info
        assert "created" in info
        assert "modified" in info

    def test_get_file_info_error(self, invalid_file_path):
        """Test getting file info for a non-existent file."""
        info = get_file_info(invalid_file_path)

        # Verify error info
        assert info["name"] == os.path.basename(invalid_file_path)
        assert info["path"] == invalid_file_path
        assert "error" in info
        assert info["exists"] is False