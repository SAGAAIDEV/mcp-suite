"""Tests for Redis client module."""

import logging
from unittest.mock import MagicMock, patch

import pytest
import redis

from src.mcp_suite.redis.client import (
    close_redis_connection,
    connect_to_redis,
    parse_redis_url,
    redis_client as global_redis_client
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


@patch("src.mcp_suite.redis.client.redis_client", None)
@patch("src.mcp_suite.redis.client.logging")
def test_connect_to_redis_success(mock_logging):
    """Test successful Redis connection."""
    # Create mock objects
    mock_client = MagicMock()
    mock_client.ping.return_value = True

    # Mock Redis.Redis to return our mock client
    with patch("src.mcp_suite.redis.client.redis.Redis", return_value=mock_client):
        # Mock parse_redis_url to return known values
        with patch("src.mcp_suite.redis.client.parse_redis_url",
                  return_value=("localhost", 6379, "password", 0)):
            # Mock REDIS.URL
            with patch("src.mcp_suite.redis.client.REDIS.URL", "redis://localhost:6379"):
                # Call the function
                result = connect_to_redis()

                # Verify the result is our mock client
                assert result is mock_client
                # Verify logging was called
                mock_logging.info.assert_called_once()


@patch("src.mcp_suite.redis.client.redis_client", None)
@patch("src.mcp_suite.redis.client.logging")
def test_connect_to_redis_custom_params(mock_logging):
    """Test Redis connection with custom parameters."""
    # Create mock objects
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_redis = MagicMock(return_value=mock_client)

    # Custom parameters
    custom_host = "custom-host"
    custom_port = 6380
    custom_password = "custom-password"
    custom_db = 2

    with patch("src.mcp_suite.redis.client.redis.Redis", mock_redis):
        # Call the function with custom parameters
        result = connect_to_redis(
            host=custom_host, port=custom_port, password=custom_password, db=custom_db
        )

        # Verify Redis.Redis was called with the correct parameters
        mock_redis.assert_called_once_with(
            host=custom_host,
            port=custom_port,
            password=custom_password,
            db=custom_db,
            decode_responses=True,
        )

        # Verify the result is our mock client
        assert result is mock_client
        # Verify logging was called
        mock_logging.info.assert_called_once()


@patch("src.mcp_suite.redis.client.redis_client", None)
@patch("src.mcp_suite.redis.client.logging")
def test_connect_to_redis_connection_error(mock_logging):
    """Test Redis connection failure."""
    # Create mock objects
    mock_client = MagicMock()
    mock_client.ping.side_effect = redis.ConnectionError("Connection refused")

    with patch("src.mcp_suite.redis.client.redis.Redis", return_value=mock_client):
        # Call the function
        result = connect_to_redis()

        # Verify the result is None
        assert result is None
        # Verify error was logged
        mock_logging.error.assert_called_once()


@patch("src.mcp_suite.redis.client.logging")
def test_close_redis_connection_success(mock_logging):
    """Test successful Redis connection closure."""
    # Create a mock client
    mock_client = MagicMock()

    # Patch the global redis_client
    with patch("src.mcp_suite.redis.client.redis_client", mock_client):
        # Call the function
        close_redis_connection()

        # Verify client.close was called
        mock_client.close.assert_called_once()
        # Verify logging was called
        mock_logging.info.assert_called_once()


@patch("src.mcp_suite.redis.client.logging")
def test_close_redis_connection_error(mock_logging):
    """Test Redis connection closure with error."""
    # Create a mock client that raises an exception on close
    mock_client = MagicMock()
    mock_client.close.side_effect = Exception("Close error")

    # Patch the global redis_client
    with patch("src.mcp_suite.redis.client.redis_client", mock_client):
        # Call the function
        close_redis_connection()

        # Verify client.close was called
        mock_client.close.assert_called_once()
        # Verify error was logged
        mock_logging.error.assert_called_once()


def test_close_redis_connection_none():
    """Test closing Redis connection when client is None."""
    # Patch the global redis_client to be None
    with patch("src.mcp_suite.redis.client.redis_client", None):
        # Call the function - should not raise any exceptions
        close_redis_connection()
