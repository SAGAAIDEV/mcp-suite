"""
Tests for the launch.py module.
"""

from unittest.mock import patch

import pytest

from src.mcp_suite.launch import (
    main,
    parse_redis_url,
)


def test_main():
    """Test the main function."""
    with patch("src.mcp_suite.launch.logger") as mock_logger:
        with patch("src.mcp_suite.launch.setup_directories") as mock_setup_directories:
            with patch(
                "src.mcp_suite.launch.configure_logger"
            ) as mock_configure_logger:
                # Call the main function
                result = main()

                # Verify the result
                assert (
                    result == "Hello from mcp-suite! "
                    "(Redis functionality has been restructured)"
                )

                # Verify logger was called
                mock_logger.info.assert_any_call(
                    "Redis functionality has been removed or restructured"
                )

                # Verify setup_directories was called
                mock_setup_directories.assert_called_once()

                # Verify configure_logger was called
                mock_configure_logger.assert_called_once()


def test_parse_redis_url_invalid_db():
    """Test parse_redis_url with invalid DB number."""
    with patch("src.mcp_suite.launch.logger") as mock_logger:
        host, port, password, db = parse_redis_url("redis://localhost/invalid")
        assert host == "localhost"
        assert port == 6379
        assert password is None
        assert db == 0
        mock_logger.warning.assert_called_once()


# Skip tests for removed functionality
@pytest.mark.skip(reason="Redis functionality has been removed")
def test_connect_to_redis():
    """Test the connect_to_redis function."""


@pytest.mark.skip(reason="Redis functionality has been removed")
def test_connect_to_redis_failure():
    """Test the connect_to_redis function when connection fails."""


@pytest.mark.skip(reason="Redis functionality has been removed")
def test_launch_redis_server_already_running():
    """Test the launch_redis_server function when Redis is already running."""


@pytest.mark.skip(reason="Redis functionality has been removed")
def test_launch_redis_server_new_instance():
    """Test the launch_redis_server function when launching a new Redis instance."""


@pytest.mark.skip(reason="Redis functionality has been removed")
def test_main_redis_connection_failure():
    """Test the main function when Redis connection fails."""


@pytest.mark.skip(reason="Redis functionality has been removed")
def test_main_with_pytest_module():
    """Test main function when running under pytest."""


@pytest.mark.skip(reason="Redis functionality has been removed")
def test_main_redis_connection_failure_with_pytest():
    """Test main function with Redis connection failure when running under pytest."""


@pytest.mark.skip(reason="Redis functionality has been removed")
def test_main_redis_connection_failure_without_pytest():
    """Test main function with Redis connection failure when not running under pytest."""


@pytest.mark.skip(reason="Redis functionality has been removed")
def test_main_redis_server_launch_failure():
    """Test main function when Redis server launch fails."""
