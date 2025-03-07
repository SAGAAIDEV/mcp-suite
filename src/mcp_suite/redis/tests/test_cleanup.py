"""Tests for Redis cleanup module."""

import signal
from unittest.mock import patch

from src.mcp_suite.redis.cleanup import (
    cleanup,
    register_cleanup_handlers,
    signal_handler,
)


@patch("src.mcp_suite.redis.cleanup.close_redis_connection")
@patch("src.mcp_suite.redis.cleanup.shutdown_redis_server")
@patch("src.mcp_suite.redis.cleanup.cleanup_logger")
def test_cleanup(mock_cleanup_logger, mock_shutdown_server, mock_close_connection):
    """Test cleanup function calls all required cleanup functions."""
    cleanup()

    # Verify all cleanup functions were called
    mock_close_connection.assert_called_once()
    mock_shutdown_server.assert_called_once()
    mock_cleanup_logger.assert_called_once()


@patch("src.mcp_suite.redis.cleanup.cleanup")
@patch("src.mcp_suite.redis.cleanup.sys.exit")
def test_signal_handler(mock_exit, mock_cleanup):
    """Test signal handler performs cleanup and exits."""
    # Test signal handler with SIGINT
    signal_handler(signal.SIGINT, None)

    # Verify cleanup was called
    mock_cleanup.assert_called_once()

    # Verify sys.exit was called with 0
    mock_exit.assert_called_once_with(0)


@patch("src.mcp_suite.redis.cleanup.atexit.register")
@patch("src.mcp_suite.redis.cleanup.signal.signal")
def test_register_cleanup_handlers(mock_signal, mock_atexit_register):
    """Test registration of cleanup handlers."""
    register_cleanup_handlers()

    # Verify atexit.register was called with cleanup function
    mock_atexit_register.assert_called_once_with(cleanup)

    # Verify signal.signal was called twice (for SIGINT and SIGTERM)
    assert mock_signal.call_count == 2

    # Verify signal handlers were registered for SIGINT and SIGTERM
    mock_signal.assert_any_call(signal.SIGINT, signal_handler)
    mock_signal.assert_any_call(signal.SIGTERM, signal_handler)
