"""Tests for Redis client module."""

import sys
from unittest.mock import MagicMock, patch

import pytest
import redis

from src.mcp_suite.redis.client import (
    close_redis_connection,
    connect_to_redis,
    parse_redis_url,
)


def test_parse_redis_url_complete():
    """Test parsing a complete Redis URL."""
    url = "redis://:password123@localhost:6380/2"
    host, port, password, db = parse_redis_url(url)

    assert host == "localhost"
    assert port == 6380
    assert password == "password123"
    assert db == 2


def test_parse_redis_url_minimal():
    """Test parsing a minimal Redis URL."""
    url = "redis://localhost"
    host, port, password, db = parse_redis_url(url)

    assert host == "localhost"
    assert port == 6379
    assert password is None
    assert db == 0


def test_parse_redis_url_invalid_db():
    """Test parsing a Redis URL with invalid DB number."""
    url = "redis://localhost/invalid"
    host, port, password, db = parse_redis_url(url)

    assert host == "localhost"
    assert port == 6379
    assert password is None
    assert db == 0  # Default to 0 for invalid DB


def test_connect_to_redis_success():
    """Test successful Redis connection."""
    # Create mock objects
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_redis_class = MagicMock(return_value=mock_client)
    mock_parse_url = MagicMock(return_value=("localhost", 6379, "password", 0))
    mock_redis_config = MagicMock()
    mock_redis_config.URL = "redis://localhost:6379/0"
    mock_logging = MagicMock()

    # Apply patches
    with patch("src.mcp_suite.redis.client.redis.Redis", mock_redis_class), \
         patch("src.mcp_suite.redis.client.parse_redis_url", mock_parse_url), \
         patch("src.mcp_suite.redis.client.REDIS", mock_redis_config), \
         patch("src.mcp_suite.redis.client.logging", mock_logging), \
         patch("src.mcp_suite.redis.client.redis_client", None):

        # Test the function directly
        # This bypasses the module-level imports which might be causing issues
        from src.mcp_suite.redis.client import connect_to_redis as direct_connect
        result = direct_connect()

    # Verify Redis client was created with correct parameters
    mock_redis_class.assert_called_once()
    assert result is mock_client


def test_connect_to_redis_custom_params():
    """Test Redis connection with custom parameters."""
    # Create mock objects
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_redis_class = MagicMock(return_value=mock_client)
    mock_redis_config = MagicMock()
    mock_redis_config.URL = "redis://localhost:6379/0"
    mock_logging = MagicMock()

    # Custom parameters
    custom_host = "custom-host"
    custom_port = 6380
    custom_password = "custom-password"
    custom_db = 2

    # Apply patches
    with patch("src.mcp_suite.redis.client.redis.Redis", mock_redis_class), \
         patch("src.mcp_suite.redis.client.REDIS", mock_redis_config), \
         patch("src.mcp_suite.redis.client.logging", mock_logging), \
         patch("src.mcp_suite.redis.client.redis_client", None):

        # Test the function directly
        from src.mcp_suite.redis.client import connect_to_redis as direct_connect
        result = direct_connect(
            host=custom_host, port=custom_port, password=custom_password, db=custom_db
        )

    # Verify Redis client was created with custom parameters
    mock_redis_class.assert_called_once_with(
        host=custom_host,
        port=custom_port,
        password=custom_password,
        db=custom_db,
        decode_responses=True,
    )
    assert result is mock_client


def test_connect_to_redis_connection_error():
    """Test Redis connection failure."""
    # Mock Redis client to raise ConnectionError
    mock_client = MagicMock()
    mock_client.ping.side_effect = redis.ConnectionError("Connection refused")
    mock_redis_class = MagicMock(return_value=mock_client)
    mock_logging = MagicMock()

    with patch("src.mcp_suite.redis.client.redis.Redis", mock_redis_class), \
         patch("src.mcp_suite.redis.client.logging", mock_logging), \
         patch("src.mcp_suite.redis.client.redis_client", None):
        result = connect_to_redis()

    # Verify result is None on connection error
    assert result is None


def test_close_redis_connection_success():
    """Test successful Redis connection closure."""
    # Create a mock client
    mock_client = MagicMock()
    mock_logging = MagicMock()

    # Test closing connection
    with patch("src.mcp_suite.redis.client.redis_client", mock_client), \
         patch("src.mcp_suite.redis.client.logging", mock_logging):
        # Import client module inside the patch to ensure correct patching
        from src.mcp_suite.redis.client import close_redis_connection as direct_close
        direct_close()

    # Verify client was closed
    mock_client.close.assert_called_once()
    mock_logging.info.assert_called_once()


def test_close_redis_connection_error():
    """Test Redis connection closure with error."""
    # Create a mock client that raises an exception on close
    mock_client = MagicMock()
    mock_client.close.side_effect = Exception("Close error")
    mock_logging = MagicMock()

    # Test closing connection
    with patch("src.mcp_suite.redis.client.redis_client", mock_client), \
         patch("src.mcp_suite.redis.client.logging", mock_logging):
        # Import client module inside the patch to ensure correct patching
        from src.mcp_suite.redis.client import close_redis_connection as direct_close
        direct_close()

    # Verify client.close was still called
    mock_client.close.assert_called_once()
    mock_logging.error.assert_called_once()


def test_close_redis_connection_none():
    """Test closing Redis connection when client is None."""
    mock_logging = MagicMock()

    # Test closing connection when client is None
    with patch("src.mcp_suite.redis.client.redis_client", None), \
         patch("src.mcp_suite.redis.client.logging", mock_logging):
        close_redis_connection()

    # No exception should be raised
    # No logging calls should be made since client is None
    mock_logging.info.assert_not_called()
    mock_logging.error.assert_not_called()
