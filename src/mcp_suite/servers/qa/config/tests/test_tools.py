"""
Tests for the tools module.
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from mcp_suite.servers.qa.config.tools import (
    clear_logs,
    get_current_log_file,
    read_log,
)


class TestGetCurrentLogFile:
    """Tests for get_current_log_file function."""

    def test_get_current_log_file(self):
        """Test getting the current log file."""
        # Test with mock path
        with patch(
            "mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", Path("/tmp/test.log")
        ):
            result = get_current_log_file()
            assert result == Path("/tmp/test.log")

        # Test with None
        with patch("mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", None):
            result = get_current_log_file()
            assert result is None


class TestReadLog:
    """Tests for read_log function."""

    def test_read_log_no_current_log_file(self):
        """Test read_log when no current log file is set."""
        with patch("mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", None):
            result = read_log()
            assert result is None

    def test_read_log_no_log_files(self):
        """Test read_log when no log files exist."""
        mock_path = MagicMock(spec=Path)
        mock_path.parent.glob.return_value = []

        with patch("mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", mock_path):
            result = read_log()
            assert result is None

    def test_read_log_invalid_index(self):
        """Test read_log with invalid index."""
        mock_path = MagicMock(spec=Path)
        mock_file = MagicMock(spec=Path)
        mock_file.is_file.return_value = True
        mock_file.stat.return_value.st_mtime = 123
        mock_path.parent.glob.return_value = [mock_file]

        with patch("mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", mock_path):
            # Test with too large index
            result = read_log(1)
            assert result is None

            # Test with too small index
            result = read_log(-2)
            assert result is None

    def test_read_log_success(self):
        """Test read_log success case."""
        mock_path = MagicMock(spec=Path)
        mock_file = MagicMock(spec=Path)
        mock_file.is_file.return_value = True
        mock_file.stat.return_value.st_mtime = 123
        mock_path.parent.glob.return_value = [mock_file]

        mock_content = ['{"level": "INFO", "message": "Test"}\n']
        mock_open_func = mock_open(read_data="".join(mock_content))

        with patch("mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", mock_path):
            with patch("builtins.open", mock_open_func):
                result = read_log(0)
                assert result is not None
                assert result["file_path"] == mock_file
                assert result["entry_count"] == 1
                assert result["entries"][0]["message"] == "Test"

    def test_read_log_json_error(self):
        """Test read_log with JSON parsing error."""
        mock_path = MagicMock(spec=Path)
        mock_file = MagicMock(spec=Path)
        mock_file.is_file.return_value = True
        mock_file.stat.return_value.st_mtime = 123
        mock_path.parent.glob.return_value = [mock_file]

        # Invalid JSON content
        mock_content = [
            '{"level": "INFO", "message": "Test"\n'
        ]  # Missing closing brace
        mock_open_func = mock_open(read_data="".join(mock_content))

        with patch("mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", mock_path):
            with patch("builtins.open", mock_open_func):
                with patch(
                    "mcp_suite.servers.qa.config.tools.logger.warning"
                ) as mock_warning:
                    result = read_log(0)
                    assert result is not None
                    assert result["entry_count"] == 0
                    mock_warning.assert_called_once()

    def test_read_log_file_error(self):
        """Test read_log with file reading error."""
        mock_path = MagicMock(spec=Path)
        mock_file = MagicMock(spec=Path)
        mock_file.is_file.return_value = True
        mock_file.stat.return_value.st_mtime = 123
        mock_path.parent.glob.return_value = [mock_file]

        with patch("mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", mock_path):
            with patch("builtins.open", side_effect=Exception("Test error")):
                with patch(
                    "mcp_suite.servers.qa.config.tools.logger.error"
                ) as mock_error:
                    result = read_log(0)
                    assert result is None
                    mock_error.assert_called_once()


class TestClearLogs:
    """Tests for clear_logs function."""

    def test_clear_logs_no_current_log_file(self):
        """Test clear_logs when no current log file is set."""
        with patch("mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", None):
            with patch(
                "mcp_suite.servers.qa.config.tools.logger.warning"
            ) as mock_warning:
                result = clear_logs()
                assert result == 0
                mock_warning.assert_called_once()

    def test_clear_logs_no_other_logs(self):
        """Test clear_logs when no other log files exist."""
        mock_path = MagicMock(spec=Path)
        mock_path.parent.glob.return_value = [mock_path]  # Only current log

        with patch("mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", mock_path):
            result = clear_logs()
            assert result == 0

    def test_clear_logs_success(self):
        """Test clear_logs success case."""
        mock_current = MagicMock(spec=Path)
        mock_other1 = MagicMock(spec=Path)
        mock_other1.is_file.return_value = True
        mock_other2 = MagicMock(spec=Path)
        mock_other2.is_file.return_value = True

        # Set up glob to return current log and two other logs
        mock_current.parent.glob.return_value = [mock_current, mock_other1, mock_other2]

        with patch("mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", mock_current):
            result = clear_logs()
            assert result == 2
            mock_other1.unlink.assert_called_once()
            mock_other2.unlink.assert_called_once()

    def test_clear_logs_with_error(self):
        """Test clear_logs with file deletion error."""
        mock_current = MagicMock(spec=Path)
        mock_other = MagicMock(spec=Path)
        mock_other.is_file.return_value = True
        mock_other.unlink.side_effect = Exception("Test error")

        # Set up glob to return current log and one other log
        mock_current.parent.glob.return_value = [mock_current, mock_other]

        with patch("mcp_suite.servers.qa.config.tools.CURRENT_LOG_FILE", mock_current):
            with patch("mcp_suite.servers.qa.config.tools.logger.error") as mock_error:
                result = clear_logs()
                assert result == 0
                mock_error.assert_called_once()
