"""Tests for the Redis utilities module."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from loguru import logger

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
    with patch.object(Path, "exists", return_value=False) as mock_exists:
        with patch.object(Path, "mkdir") as mock_mkdir:
            yield mock_exists, mock_mkdir


@pytest.fixture
def mock_logger():
    """Mock the logger."""
    with patch("mcp_suite.redis.utils.logger") as mock_log:
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

    # Call the function
    utils.setup_directories()

    # Check that mkdir was called twice (once for logs, once for db)
    assert mock_mkdir.call_count == 2
    mock_mkdir.assert_any_call(parents=True, exist_ok=True)

    # Check logs were written
    assert mock_logger.info.call_count >= 2


def test_setup_directories_permission_error(mock_logger):
    """Test setup_directories handles permission errors."""
    # Mock Path.exists to return False (directories don't exist)
    with patch.object(Path, "exists", return_value=False):
        # Mock Path.mkdir to raise PermissionError on first and third calls
        mkdir_mock = MagicMock(side_effect=[PermissionError, None, PermissionError, None])
        with patch.object(Path, "mkdir", mkdir_mock):
            # Call the function
            utils.setup_directories()

    # Check that warning was logged for fallback directories
    assert mock_logger.warning.call_count == 2


def test_configure_logger_first_time(reset_logger_state):
    """Test configure_logger when called for the first time."""
    # Create mock objects for logger.add and logger.remove
    with patch("loguru.logger.add", return_value=1) as mock_add:
        with patch("loguru.logger.remove") as mock_remove:
            with patch("mcp_suite.redis.utils.logger") as mock_logger:
                # Set up the test state
                utils.logger_configured = False
                utils.logger_ids = []

                # Call the function
                utils.configure_logger()

                # Verify logger.remove was called
                mock_remove.assert_called_once()
                # Verify logger.add was called at least once
                assert mock_add.call_count >= 1


def test_configure_logger_already_configured(reset_logger_state, mock_logger):
    """Test configure_logger when logger is already configured."""
    with patch("loguru.logger.add") as mock_add:
        # Set up the test state
        utils.logger_configured = True

        # Call the function
        utils.configure_logger()

        # Verify logger.add was not called
        mock_add.assert_not_called()


def test_configure_logger_file_exception(reset_logger_state):
    """Test configure_logger when adding file logger raises exception."""
    # Mock logger.add to return 1 for the first call and raise Exception for the second call
    add_mock = MagicMock(side_effect=[1, Exception("File error")])

    with patch("loguru.logger.add", add_mock):
        with patch("loguru.logger.remove"):
            with patch("mcp_suite.redis.utils.logger") as mock_logger:
                # Set up the test state
                utils.logger_configured = False
                utils.logger_ids = []

                # Call the function
                utils.configure_logger()

                # Verify warning was logged
                mock_logger.warning.assert_called_once()


def test_cleanup_logger(reset_logger_state):
    """Test cleanup_logger properly cleans up resources."""
    with patch("loguru.logger.remove") as mock_remove:
        # Set up the test state
        utils.logger_configured = True
        utils.logger_ids = [1, 2]

        # Call the function
        utils.cleanup_logger()

        # Verify logger.remove was called
        mock_remove.assert_called_once()
        # Verify state was reset
        assert not utils.logger_configured
        assert len(utils.logger_ids) == 0


def test_get_db_dir():
    """Test get_db_dir returns the correct path."""
    # Call the function
    result = utils.get_db_dir()

    # Verify the result
    assert result == utils.db_dir
    assert isinstance(result, Path)
