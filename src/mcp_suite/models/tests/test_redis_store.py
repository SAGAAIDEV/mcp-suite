"""
Tests for the Redis store module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic_redis.asyncio import RedisConfig

from mcp_suite.models.redis_store import (
    close_redis_store,
    get_redis_store,
    parse_redis_url,
)


class TestRedisStore:
    """Tests for the Redis store module."""

    def test_parse_redis_url(self):
        """Test parsing Redis URLs into connection parameters."""
        # Test with full URL
        url = "redis://username:password@hostname:6380/5"
        result = parse_redis_url(url)
        assert result["host"] == "hostname"
        assert result["port"] == 6380
        assert result["db"] == 5
        assert result["password"] == "password"

        # Test with minimal URL
        url = "redis://localhost"
        result = parse_redis_url(url)
        assert result["host"] == "localhost"
        assert result["port"] == 6379
        assert result["db"] == 0
        assert result["password"] is None

        # Test with custom port
        url = "redis://redis-server:7000"
        result = parse_redis_url(url)
        assert result["host"] == "redis-server"
        assert result["port"] == 7000
        assert result["db"] == 0
        assert result["password"] is None

        # Test with custom db
        url = "redis://localhost/3"
        result = parse_redis_url(url)
        assert result["host"] == "localhost"
        assert result["port"] == 6379
        assert result["db"] == 3
        assert result["password"] is None

    @pytest.mark.asyncio
    @patch("mcp_suite.models.redis_store.REDIS")
    @patch("mcp_suite.models.redis_store.Store")
    async def test_get_redis_store_with_env_config(self, mock_store, mock_redis):
        """Test getting Redis store with environment configuration."""
        # Setup mock
        mock_redis.URL = "redis://test-host:1234/2"
        mock_store_instance = MagicMock()
        mock_store.return_value = mock_store_instance

        # Call function
        get_redis_store()

        # Verify store was created with correct parameters
        mock_store.assert_called_once()
        args, kwargs = mock_store.call_args
        assert kwargs["name"] == "mcp_suite"
        assert kwargs["life_span_in_seconds"] == 86400

        # Verify Redis config was created with parsed URL
        redis_config = kwargs["redis_config"]
        assert redis_config.host == "test-host"
        assert redis_config.port == 1234
        assert redis_config.db == 2

        # Call again to test singleton behavior
        get_redis_store()
        assert mock_store.call_count == 1  # Should not be called again

    @pytest.mark.asyncio
    @patch("mcp_suite.models.redis_store.REDIS", None)
    @patch("mcp_suite.models.redis_store.Store")
    async def test_get_redis_store_with_defaults(self, mock_store):
        """Test getting Redis store with default configuration."""
        # Reset the global store
        import mcp_suite.models.redis_store

        mcp_suite.models.redis_store._store = None

        # Setup mock
        mock_store_instance = MagicMock()
        mock_store.return_value = mock_store_instance

        # Call function
        get_redis_store()

        # Verify store was created with correct parameters
        mock_store.assert_called_once()
        args, kwargs = mock_store.call_args
        assert kwargs["name"] == "mcp_suite"
        assert kwargs["life_span_in_seconds"] == 86400

        # Verify Redis config was created with defaults
        redis_config = kwargs["redis_config"]
        assert isinstance(redis_config, RedisConfig)

    @pytest.mark.asyncio
    @patch("mcp_suite.models.redis_store._store")
    async def test_close_redis_store(self, mock_store):
        """Test closing the Redis store connection."""
        # Setup mock
        mock_store.close = AsyncMock()

        # Call function
        await close_redis_store()

        # Verify store was closed
        mock_store.close.assert_called_once()

        # Test with no store
        import mcp_suite.models.redis_store

        mcp_suite.models.redis_store._store = None

        # Should not raise an exception
        await close_redis_store()
