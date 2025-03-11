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


# Ensure that .mp3 files are supported for tests
@pytest.fixture(autouse=True)
def override_supported_formats(monkeypatch):
    monkeypatch.setattr(
        "src.mcp_suite.servers.transcriber.utils.file_utils.SUPPORTED_FORMATS",
        {".mp3", ".wav"},
    )


@pytest.fixture
def test_audio_file():
    """Create a temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(b"test audio content")
        temp_path = temp_file.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestValidateAudioFile:
    """Tests for the validate_audio_file function."""

    def test_valid_file(self, test_audio_file):
        """Test validation with a valid audio file."""
        is_valid, error_message = validate_audio_file(test_audio_file)
        assert is_valid is True
        assert error_message == ""

    def test_file_not_found(self):
        """Test validation with a non-existent file."""
        non_existent = "/path/to/nonexistent/file.mp3"
        is_valid, error_message = validate_audio_file(non_existent)
        assert is_valid is False
        assert "not found" in error_message

    def test_not_a_file(self, tmp_path):
        """Test validation with a directory instead of a file."""
        is_valid, error_message = validate_audio_file(str(tmp_path))
        assert is_valid is False
        assert "not a file" in error_message

    def test_unsupported_format(self, test_audio_file):
        """Test validation with an unsupported file format."""
        unsupported_file = test_audio_file.replace(".mp3", ".xyz")
        os.rename(test_audio_file, unsupported_file)
        try:
            is_valid, error_message = validate_audio_file(unsupported_file)
            assert is_valid is False
            assert "Unsupported audio format" in error_message
        finally:
            if os.path.exists(unsupported_file):
                os.unlink(unsupported_file)

    def test_unreadable_file(self, test_audio_file):
        """Test validation with an unreadable file."""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            is_valid, error_message = validate_audio_file(test_audio_file)
            assert is_valid is False
            assert "not readable" in error_message

    def test_uppercase_extension(self, test_audio_file):
        """Test validation with an uppercase file extension."""
        uppercase_file = test_audio_file.replace(".mp3", ".MP3")
        os.rename(test_audio_file, uppercase_file)
        try:
            is_valid, error_message = validate_audio_file(uppercase_file)
            assert is_valid is True
            assert error_message == ""
        finally:
            if os.path.exists(uppercase_file):
                os.unlink(uppercase_file)


class TestGetFileSize:
    """Tests for the get_file_size function."""

    def test_get_size_success(self, test_audio_file):
        """Test getting the size of a valid file."""
        size = get_file_size(test_audio_file)
        expected_size = os.path.getsize(test_audio_file)
        assert size > 0
        assert size == expected_size

    def test_get_size_nonexistent_file(self):
        """Test getting the size of a non-existent file."""
        size = get_file_size("/path/to/nonexistent/file.mp3")
        assert size == 0

    def test_get_size_exception(self, monkeypatch):
        """Test get_file_size when os.path.getsize raises an exception."""

        def fake_getsize(path):
            raise Exception("Fake exception")

        monkeypatch.setattr(os.path, "getsize", fake_getsize)
        size = get_file_size("dummy")
        assert size == 0


class TestGetFileInfo:
    """Tests for the get_file_info function."""

    def test_get_info_success(self, test_audio_file):
        """Test getting information for a valid file."""
        info = get_file_info(test_audio_file)
        assert info["name"] == os.path.basename(test_audio_file)
        assert info["path"] == str(Path(test_audio_file).absolute())
        assert info["size"] > 0
        assert "MB" in info["size_human"]
        assert info["extension"] == ".mp3"
        assert info["exists"] is True
        assert info["is_file"] is True

    def test_get_info_error(self):
        """Test getting information for a non-existent file."""
        nonexistent_file = "/path/to/nonexistent/file.mp3"
        info = get_file_info(nonexistent_file)
        assert info["name"] == os.path.basename(nonexistent_file)
        assert info["path"] == nonexistent_file
        assert "error" in info
        assert info["exists"] is False

    def test_get_info_exception(self, test_audio_file, monkeypatch):
        """Test get_file_info when Path.stat raises an exception."""
        original_stat = Path.stat

        def fake_stat(self):
            raise Exception("Fake stat error")

        monkeypatch.setattr(Path, "stat", fake_stat)
        info = get_file_info(test_audio_file)
        assert "error" in info
        # Restore the original stat method
        monkeypatch.setattr(Path, "stat", original_stat)
