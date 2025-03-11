import os

# Set environment variables required by the configuration (pydantic settings)
os.environ["CLIENT_ID"] = "dummy_client_id"
os.environ["CLIENT_SECRET"] = "dummy_client_secret"
os.environ["LLM_API_KEYS"] = '{"API_KEY": "dummy_api_key"}'

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
    """Test that cleanup() calls all required cleanup functions."""
    cleanup()
    # Verify that all cleanup functions were called exactly once
    mock_close_connection.assert_called_once()
    mock_shutdown_server.assert_called_once()
    mock_cleanup_logger.assert_called_once()


@patch("src.mcp_suite.redis.cleanup.cleanup")
@patch("src.mcp_suite.redis.cleanup.logger")
@patch("src.mcp_suite.redis.cleanup.sys.exit")
def test_signal_handler_sigint(mock_sys_exit, mock_logger, mock_cleanup):
    """Test signal_handler for SIGINT: logs, calls cleanup, and exits."""
    sig = signal.SIGINT
    dummy_frame = object()
    signal_handler(sig, dummy_frame)
    # Verify that the logger logged the correct message for SIGINT
    mock_logger.info.assert_called_once_with(f"Received signal {sig}, shutting down")
    # Verify that cleanup() was called
    mock_cleanup.assert_called_once()
    # Verify that sys.exit was called with exit code 0
    mock_sys_exit.assert_called_once_with(0)


@patch("src.mcp_suite.redis.cleanup.cleanup")
@patch("src.mcp_suite.redis.cleanup.logger")
@patch("src.mcp_suite.redis.cleanup.sys.exit")
def test_signal_handler_sigterm(mock_sys_exit, mock_logger, mock_cleanup):
    """Test signal_handler for SIGTERM: logs, calls cleanup, and exits."""
    sig = signal.SIGTERM
    dummy_frame = object()
    signal_handler(sig, dummy_frame)
    # Verify that the logger logged the correct message for SIGTERM
    mock_logger.info.assert_called_once_with(f"Received signal {sig}, shutting down")
    # Verify that cleanup() was called
    mock_cleanup.assert_called_once()
    # Verify that sys.exit was called with exit code 0
    mock_sys_exit.assert_called_once_with(0)


@patch("src.mcp_suite.redis.cleanup.atexit.register")
@patch("src.mcp_suite.redis.cleanup.signal.signal")
def test_register_cleanup_handlers(mock_signal, mock_atexit_register):
    """Test that register_cleanup_handlers properly registers exit and signal handlers."""
    register_cleanup_handlers()
    # Verify that atexit.register was called with cleanup function
    mock_atexit_register.assert_called_once_with(cleanup)
    # Verify that signal.signal was called twice (for SIGINT and SIGTERM)
    assert mock_signal.call_count == 2
    mock_signal.assert_any_call(signal.SIGINT, signal_handler)
    mock_signal.assert_any_call(signal.SIGTERM, signal_handler)
