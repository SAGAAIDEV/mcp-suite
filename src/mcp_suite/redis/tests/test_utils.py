"""Tests for the Redis utilities module."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mcp_suite.redis import utils


@pytest.fixture
def reset_utils_state():
    """Reset the global state in utils module between tests."""
    # Save original values
    original_logger_ids = utils.logger_ids.copy()
    original_logger_configured = utils.logger_configured
    original_logs_dir = utils.logs_dir
    original_db_dir = utils.db_dir

    # Reset for test
    utils.logger_ids = []
    utils.logger_configured = False

    yield

    # Restore original values after test
    utils.logger_ids = original_logger_ids
    utils.logger_configured = original_logger_configured
    utils.logs_dir = original_logs_dir
    utils.db_dir = original_db_dir


@pytest.fixture
def mock_path():
    """Mock Path.exists and Path.mkdir."""
    mock_exists = MagicMock(return_value=False)
    mock_mkdir = MagicMock()

    with patch("pathlib.Path.exists", mock_exists), \
         patch("pathlib.Path.mkdir", mock_mkdir):
        yield mock_exists, mock_mkdir


@pytest.fixture
def mock_logger():
    """Mock the logger."""
    mock_log = MagicMock()
    with patch("mcp_suite.redis.utils.logger", mock_log):
        yield mock_log


@pytest.fixture
def reset_logger_state():
    """Reset logger state between tests."""
    # Save original state
    original_ids = utils.logger_ids.copy()
    original_configured = utils.logger_configured

    # Return control to the test
    yield

    # Restore original state
    utils.logger_ids.clear()
    utils.logger_ids.extend(original_ids)
    utils.logger_configured = original_configured


def test_setup_directories(mock_path, mock_logger):
    """Test setup_directories creates logs and db directories."""
    mock_exists, mock_mkdir = mock_path

    # Ensure the logger is properly mocked
    mock_logger.info.reset_mock()

    utils.setup_directories()

    # Check that mkdir was called twice (once for logs, once for db)
    assert mock_mkdir.call_count == 2
    mock_mkdir.assert_any_call(parents=True, exist_ok=True)

    # Check logs were written
    assert mock_logger.info.call_count >= 2


def test_setup_directories_permission_error(mock_logger):
    """Test setup_directories handles permission errors."""
    mock_exists = MagicMock(return_value=False)
    mock_mkdir = MagicMock(side_effect=[PermissionError, None, PermissionError, None])

    # Ensure the logger is properly mocked
    mock_logger.warning.reset_mock()

    with patch("pathlib.Path.exists", mock_exists), patch("pathlib.Path.mkdir", mock_mkdir):
        utils.setup_directories()

    # Check that warning was logged for fallback directories
    assert mock_logger.warning.call_count == 2


def test_configure_logger_first_time(reset_logger_state):
    """Test configure_logger when called for the first time."""
    # Create mock objects
    mock_add = MagicMock(side_effect=[1, 2])  # Return IDs for tracking
    mock_remove = MagicMock()
    mock_logger = MagicMock()

    with patch("mcp_suite.redis.utils.logger_configured", False), \
         patch("mcp_suite.redis.utils.logger_ids", []), \
         patch("loguru.logger.add", mock_add), \
         patch("loguru.logger.remove", mock_remove), \
         patch("mcp_suite.redis.utils.logger", mock_logger):

        # Import the module inside the patch to ensure patches take effect
        from mcp_suite.redis import utils
        utils.configure_logger()

        # Check logger was configured correctly
        mock_remove.assert_called_once()
        assert mock_add.call_count == 2

        # First call should be to stderr
        assert mock_add.call_args_list[0][0][0] == sys.stderr

        # Second call should be to log file
        assert str(utils.logs_dir) in str(mock_add.call_args_list[1][0][0])


def test_configure_logger_already_configured(reset_logger_state, mock_logger):
    """Test configure_logger when logger is already configured."""
    mock_add = MagicMock()

    with patch("mcp_suite.redis.utils.logger_configured", True), \
         patch("loguru.logger.add", mock_add):

        utils.configure_logger()

        # Should not attempt to add new handlers
        mock_add.assert_not_called()


def test_configure_logger_file_exception(reset_logger_state):
    """Test configure_logger when adding file logger raises exception."""
    # Create mock objects
    mock_add = MagicMock(side_effect=[1, Exception("File error")])
    mock_logger = MagicMock()

    with patch("mcp_suite.redis.utils.logger_configured", False), \
         patch("mcp_suite.redis.utils.logger_ids", []), \
         patch("loguru.logger.add", mock_add), \
         patch("mcp_suite.redis.utils.logger", mock_logger):

        # Import the module inside the patch to ensure patches take effect
        from mcp_suite.redis import utils
        utils.configure_logger()

        # Should log warning about file logger failure
        mock_logger.warning.assert_called_once()


def test_cleanup_logger(reset_logger_state):
    """Test cleanup_logger properly cleans up resources."""
    mock_remove = MagicMock()

    with patch("mcp_suite.redis.utils.logger_configured", True), \
         patch("mcp_suite.redis.utils.logger_ids", [1, 2]), \
         patch("loguru.logger.remove", mock_remove):

        utils.cleanup_logger()

        # Should remove all handlers
        mock_remove.assert_called_once()

        # Should reset state
        assert not utils.logger_configured
        assert len(utils.logger_ids) == 0


def test_get_db_dir():
    """Test get_db_dir returns the correct path."""
    result = utils.get_db_dir()
    assert result == utils.db_dir
    assert isinstance(result, Path)
