"""Tests for Redis client module."""

import logging
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


class TestConnectToRedis:
    """Tests for connect_to_redis function."""

    @patch("src.mcp_suite.redis.client.redis.Redis")
    def test_connect_with_url(self, mock_redis):
        """Test connecting with URL parameter."""
        # Setup
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        # Execute
        with patch("src.mcp_suite.redis.client.redis_client", None):
            result = connect_to_redis(url="redis://localhost:6379")

        # Verify
        assert mock_redis.called

    @patch("src.mcp_suite.redis.client.redis.Redis")
    def test_connect_with_explicit_params(self, mock_redis):
        """Test connecting with explicit parameters."""
        # Setup
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        # Execute
        with patch("src.mcp_suite.redis.client.redis_client", None):
            result = connect_to_redis(
                host="localhost",
                port=6379,
                password="password",
                db=0
            )

        # Verify
        assert mock_redis.called


class TestCloseRedisConnection:
    """Tests for close_redis_connection function."""

    def test_close_none_client(self):
        """Test closing when client is None."""
        # Setup
        with patch("src.mcp_suite.redis.client.redis_client", None):
            # Execute & Verify (no exception should be raised)
            close_redis_connection()

    @patch("src.mcp_suite.redis.client.redis_client")
    def test_close_with_client(self, mock_client):
        """Test closing with a client."""
        # Execute
        close_redis_connection()

        # Verify
        assert mock_client.close.called