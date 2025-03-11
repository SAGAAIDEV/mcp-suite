import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch
from src.mcp_suite.servers.transcriber.utils.file_utils import (
    get_file_info,
    get_file_size,
    validate_audio_file,
)

@pytest.fixture(autouse=True)
def override_supported_formats(monkeypatch):
    monkeypatch.setattr(
        "src.mcp_suite.servers.transcriber.utils.file_utils.SUPPORTED_FORMATS",
        {".mp3", ".wav"},
    )

@pytest.fixture
def test_audio_file():
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(b"test audio content")
        temp_path = temp_file.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

class TestValidateAudioFile:
    def test_empty_supported_formats(self, test_audio_file, monkeypatch):
        monkeypatch.setattr("src.mcp_suite.servers.transcriber.utils.file_utils.SUPPORTED_FORMATS", set())
        is_valid, error_message = validate_audio_file(test_audio_file)
        assert is_valid is False
        assert "Unsupported audio format" in error_message

    def test_long_filename(self):
        long_filename = "/tmp/" + "a" * 255 + ".mp3"
        with open(long_filename, "w") as f:
            f.write("test")
        is_valid, error_message = validate_audio_file(long_filename)
        assert is_valid is True
        os.remove(long_filename)

    def test_locked_file(self, test_audio_file):
        with open(test_audio_file, "w") as f:
            is_valid, error_message = validate_audio_file(test_audio_file)
        assert is_valid is False
        assert "not readable" in error_message

    def test_file_not_found(self):
        is_valid, error_message = validate_audio_file("/nonexistent/file.mp3")
        assert is_valid is False
        assert "not found" in error_message

    def test_unreadable_file(self, test_audio_file):
        os.chmod(test_audio_file, 0o000)
        is_valid, error_message = validate_audio_file(test_audio_file)
        os.chmod(test_audio_file, 0o644)
        assert is_valid is False
        assert "not readable" in error_message

class TestGetFileSize:
    def test_directory_instead_of_file(self, tmp_path):
        size = get_file_size(str(tmp_path))
        assert size == 0

    def test_broken_symlink(self, tmp_path):
        link_path = tmp_path / "broken_link.mp3"
        link_path.symlink_to("/nonexistent/path.mp3")
        size = get_file_size(str(link_path))
        assert size == 0

    def test_get_size_exception(self, monkeypatch):
        monkeypatch.setattr(os.path, "getsize", lambda x: 1 / 0)  # Force exception
        size = get_file_size("dummy")
        assert size == 0

class TestGetFileInfo:
    def test_directory_info(self, tmp_path):
        info = get_file_info(str(tmp_path))
        assert info["is_file"] is False
        assert info["exists"] is True

    def test_file_with_no_extension(self):
        no_ext_file = "/tmp/testfile"
        with open(no_ext_file, "w") as f:
            f.write("test")
        info = get_file_info(no_ext_file)
        assert info["extension"] == ""
        os.remove(no_ext_file)

    def test_large_file(self):
        large_file = "/tmp/large_file.mp3"
        with open(large_file, "wb") as f:
            f.write(b"0" * (2 * 1024 * 1024 * 1024))  # 2GB file
        info = get_file_info(large_file)
        assert info["size"] > 2 * 1024 * 1024 * 1024
        os.remove(large_file)

    def test_get_info_exception(self, test_audio_file, monkeypatch):
        monkeypatch.setattr(Path, "stat", lambda self: 1 / 0)  # Force exception
        info = get_file_info(test_audio_file)
        assert "error" in info
