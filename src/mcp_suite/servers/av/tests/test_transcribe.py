from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest

from mcp_suite.servers.av.lib.transcribe import transcribe_media


@pytest.fixture
def mock_transcriber():
    """Fixture to mock the AssemblyAI transcriber."""
    with patch("mcp_suite.servers.av.lib.transcribe.aai.Transcriber") as mock:
        transcriber_instance = Mock()
        mock.return_value = transcriber_instance

        # Mock the transcript result
        transcript_result = Mock()
        transcript_result.text = "This is a test transcript."
        transcript_result.utterances = [
            Mock(speaker=1, text="Hello world"),
            Mock(speaker=2, text="Testing the transcription"),
        ]

        transcriber_instance.transcribe.return_value = transcript_result
        yield transcriber_instance


@pytest.fixture
def mock_path_exists():
    """Fixture to mock Path.exists to return True."""
    with patch.object(Path, "exists", return_value=True) as mock_exists:
        yield mock_exists


@pytest.fixture
def mock_path_is_file():
    """Fixture to mock Path.is_file to return True."""
    with patch.object(Path, "is_file", return_value=True) as mock_is_file:
        yield mock_is_file


def test_transcribe_media_file_not_found(mock_transcriber, mock_path_is_file):
    """Test that FileNotFoundError is raised when the file doesn't exist."""
    with patch.object(Path, "exists", return_value=False):
        with pytest.raises(FileNotFoundError) as excinfo:
            transcribe_media("nonexistent_file.mp4")

        assert "Media file not found" in str(excinfo.value)


def test_transcribe_media_not_a_file(mock_transcriber, mock_path_exists):
    """Test that ValueError is raised when the path is not a file."""
    with patch.object(Path, "is_file", return_value=False):
        with pytest.raises(ValueError) as excinfo:
            transcribe_media("directory_path")

        assert "Path is not a file" in str(excinfo.value)


def test_transcribe_media_successful(
    mock_transcriber, mock_path_exists, mock_path_is_file
):
    """Test successful transcription with default parameters."""
    result = transcribe_media("test_file.mp4")

    # Verify the transcriber was called with the correct parameters
    mock_transcriber.transcribe.assert_called_once()

    # Check that the result has the expected format
    assert result.text == "This is a test transcript."
    assert len(result.utterances) == 2
    assert result.utterances[0].speaker == 1
    assert result.utterances[0].text == "Hello world"


def test_transcribe_media_with_custom_params(
    mock_transcriber, mock_path_exists, mock_path_is_file
):
    """Test transcription with custom parameters."""
    _ = transcribe_media(
        "test_file.mp4",
        language_code="es",
        speaker_labels=True,
        punctuate=False,
        format_text=False,
    )

    # Get the config that was passed to the transcriber
    call_args = mock_transcriber.transcribe.call_args
    config = call_args[1]["config"]

    # Verify configuration was set correctly
    assert config.language_code == "es"
    assert config.speaker_labels is True
    assert config.punctuate is False
    assert config.format_text is False
    assert call_args[0][0] == "test_file.mp4"


def test_transcribe_media_with_path_object(
    mock_transcriber, mock_path_exists, mock_path_is_file
):
    """Test that the function works with Path objects."""
    path_obj = Path("test_file.mp4")

    with patch(
        "mcp_suite.servers.av.lib.transcribe.Path", return_value=path_obj
    ) as mock_path:
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.is_file.return_value = True

        _ = transcribe_media(path_obj)

        # Verify the transcriber was called with the stringified path
        mock_transcriber.transcribe.assert_called_once_with(str(path_obj), config=ANY)


if __name__ == "__main__":  # pragma: no cover
    pytest.main(["-v", "test_transcribe.py"])
