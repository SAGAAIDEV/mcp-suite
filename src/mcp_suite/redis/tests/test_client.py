"""Tests for Redis client module."""

from unittest.mock import MagicMock, patch

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


@patch("src.mcp_suite.redis.client.redis.Redis")
@patch("src.mcp_suite.redis.client.parse_redis_url")
def test_connect_to_redis_success(mock_parse_url, mock_redis_class):
    """Test successful Redis connection."""
    # Mock parse_redis_url to return test values
    mock_parse_url.return_value = ("localhost", 6379, "password", 0)

    # Mock Redis client
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_redis_class.return_value = mock_client

    # Test connection
    result = connect_to_redis()

    # Verify Redis client was created with correct parameters
    mock_redis_class.assert_called_once()
    assert result is mock_client


@patch("src.mcp_suite.redis.client.redis.Redis")
@patch("src.mcp_suite.redis.client.parse_redis_url")
def test_connect_to_redis_custom_params(mock_parse_url, mock_redis_class):
    """Test Redis connection with custom parameters."""
    # Mock parse_redis_url to return default values
    mock_parse_url.return_value = ("localhost", 6379, "password", 0)

    # Mock Redis client
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_redis_class.return_value = mock_client

    # Test connection with custom parameters
    custom_host = "custom-host"
    custom_port = 6380
    custom_password = "custom-password"
    custom_db = 2

    result = connect_to_redis(
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


@patch("src.mcp_suite.redis.client.redis.Redis")
@patch("src.mcp_suite.redis.client.parse_redis_url")
def test_connect_to_redis_connection_error(mock_parse_url, mock_redis_class):
    """Test Redis connection failure."""
    # Mock parse_redis_url to return test values
    mock_parse_url.return_value = ("localhost", 6379, "password", 0)

    # Mock Redis client to raise ConnectionError
    mock_client = MagicMock()
    mock_client.ping.side_effect = redis.ConnectionError("Connection refused")
    mock_redis_class.return_value = mock_client

    # Test connection
    result = connect_to_redis()

    # Verify result is None on connection error
    assert result is None


@patch("src.mcp_suite.redis.client.redis_client")
def test_close_redis_connection_success(mock_redis_client):
    """Test successful Redis connection closure."""
    # Test closing connection
    close_redis_connection()

    # Verify client was closed
    mock_redis_client.close.assert_called_once()


@patch("src.mcp_suite.redis.client.redis_client")
def test_close_redis_connection_error(mock_redis_client):
    """Test Redis connection closure with error."""
    # Mock client to raise exception on close
    mock_redis_client.close.side_effect = Exception("Close error")

    # Test closing connection
    close_redis_connection()

    # Verify client.close was still called
    mock_redis_client.close.assert_called_once()


@patch("src.mcp_suite.redis.client.redis_client", None)
def test_close_redis_connection_none():
    """Test closing Redis connection when client is None."""
    # Test closing connection when client is None
    close_redis_connection()
    # No exception should be raised
