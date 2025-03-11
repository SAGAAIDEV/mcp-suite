"""Tests for the Redis utilities module."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mcp_suite.redis import utils


def test_get_db_dir():
    """Test get_db_dir returns the correct path."""
    result = utils.get_db_dir()
    assert result == utils.db_dir
    assert isinstance(result, Path)


@patch("pathlib.Path.exists")
@patch("pathlib.Path.mkdir")
def test_setup_directories_success(mock_mkdir, mock_exists):
    """Test setup_directories creates directories successfully."""
    # Setup
    mock_exists.return_value = False

    # Execute
    utils.setup_directories()

    # Verify
    assert mock_mkdir.call_count >= 2
    mock_mkdir.assert_any_call(parents=True, exist_ok=True)


@patch("pathlib.Path.exists")
@patch("pathlib.Path.mkdir")
@patch("mcp_suite.redis.utils.logger")
def test_setup_directories_permission_error(mock_logger, mock_mkdir, mock_exists):
    """Test setup_directories handles permission errors."""
    # Setup
    mock_exists.return_value = False
    mock_mkdir.side_effect = [PermissionError, None, PermissionError, None]

    # Execute
    utils.setup_directories()

    # Verify
    assert mock_logger.warning.call_count >= 1


@patch("mcp_suite.redis.utils.logger_configured", False)
@patch("mcp_suite.redis.utils.logger_ids", [])
@patch("loguru.logger.add")
@patch("loguru.logger.remove")
def test_configure_logger_new(mock_remove, mock_add):
    """Test configure_logger when called for the first time."""
    # Setup
    mock_add.return_value = 1

    # Execute
    utils.configure_logger()

    # Verify
    assert utils.logger_configured is True
    assert len(utils.logger_ids) > 0


@patch("mcp_suite.redis.utils.logger_configured", True)
@patch("loguru.logger.add")
def test_configure_logger_already_configured(mock_add):
    """Test configure_logger when logger is already configured."""
    # Execute
    utils.configure_logger()

    # Verify
    mock_add.assert_not_called()


@patch("mcp_suite.redis.utils.logger_configured", True)
@patch("mcp_suite.redis.utils.logger_ids", [1, 2])
@patch("loguru.logger.remove")
def test_cleanup_logger_new(mock_remove):
    """Test cleanup_logger properly cleans up resources."""
    # Execute
    utils.cleanup_logger()

    # Verify
    assert utils.logger_configured is False
    assert len(utils.logger_ids) == 0