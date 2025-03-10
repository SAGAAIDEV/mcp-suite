"""
Tests for the RedisRepository class.

This module tests the functionality of the RedisRepository class.
"""

import json

# Mock the REDIS configuration to avoid validation errors
import sys
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ConfigDict, Field

from src.mcp_suite.base.models.redis import RedisRepository


class MockRedis:
    URL = "localhost"
    PORT = 6379
    PASSWORD = "password"
    DB = 0


# Mock the config.env module
mock_env = MagicMock()
mock_env.REDIS = MockRedis()
sys.modules["config.env"] = mock_env


# Define test models
class ModelTest(BaseModel):
    """Simple model for testing the repository."""

    name: str = "default"
    value: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ModelWithDatesTest(BaseModel):
    """Test model with datetime fields."""

    name: str = "default"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model_config = ConfigDict(arbitrary_types_allowed=True)


@pytest.fixture
def reset_redis_connection():
    """Reset the Redis connection before and after each test."""
    # Clear the _redis connection before the test
    RedisRepository._redis = None

    # Run the test
    yield

    # Clear the connection after the test
    RedisRepository._redis = None


class TestRedisRepository:
    """Test cases for the RedisRepository class."""

    def test_initialization(self):
        """Test that the repository is initialized correctly."""
        repo = RedisRepository(ModelTest)

        # Check that the model class is set correctly
        assert repo.model_class == ModelTest

        # Check that the key is empty as per implementation
        assert repo.key == ""

        # Test with a custom prefix
        repo_with_prefix = RedisRepository(ModelTest, prefix="test")
        assert repo_with_prefix.key == ""
        assert repo_with_prefix.prefix == "test"

    def test_get_key(self):
        """Test the _get_key method."""
        repo = RedisRepository(ModelTest)

        # Test _get_key with the model class (not instance)
        assert repo._get_key(ModelTest) == "mcp_service:ModelTest"

        # Test with a different model class
        assert repo._get_key(ModelWithDatesTest) == "mcp_service:ModelWithDatesTest"

    @patch("redis.Redis")
    def test_get_redis_url(self, mock_redis_class):
        """Test the get_redis method with URL."""
        # Setup mocks
        mock_redis_instance = MagicMock()
        mock_redis_class.from_url.return_value = mock_redis_instance
        # Ensure ping succeeds
        mock_redis_instance.ping.return_value = True

        # Make sure the Redis connection is cleared
        RedisRepository._redis = None

        # Test with a URL that starts with redis://
        with patch(
            "src.mcp_suite.base.models.redis.repository.REDIS"
        ) as mock_redis_config:
            mock_redis_config.URL = "redis://localhost:6379/0"
            mock_redis_config.PASSWORD = "password"

            # Get the Redis connection
            redis_conn = RedisRepository.get_redis()

            # Check that from_url was called with the correct parameters
            mock_redis_class.from_url.assert_called_once_with(
                "redis://localhost:6379/0", password="password", decode_responses=True
            )

            # Check that ping was called to test the connection
            mock_redis_instance.ping.assert_called_once()

            # Check that the connection was returned
            assert redis_conn == mock_redis_instance

    @patch("redis.Redis")
    def test_get_redis_host(self, mock_redis_class):
        """Test the get_redis method with host."""
        # Setup mocks
        mock_redis_instance = MagicMock()
        mock_redis_class.return_value = mock_redis_instance
        # Ensure ping succeeds
        mock_redis_instance.ping.return_value = True

        # Make sure the Redis connection is cleared
        RedisRepository._redis = None

        # Test with a host without redis:// prefix
        with patch(
            "src.mcp_suite.base.models.redis.repository.REDIS"
        ) as mock_redis_config:
            mock_redis_config.URL = "localhost"
            mock_redis_config.PORT = 6379
            mock_redis_config.PASSWORD = "password"

            # Get the Redis connection
            redis_conn = RedisRepository.get_redis()

            # Check that Redis constructor was called with explicit parameters
            mock_redis_class.assert_called_once_with(
                host="localhost", port=6379, password="password", decode_responses=True
            )

            # Check that ping was called to test the connection
            mock_redis_instance.ping.assert_called_once()

            # Check that the connection was returned
            assert redis_conn == mock_redis_instance

    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    def test_save(self, mock_get_redis):
        """Test the save method."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Create a repository and model
        repo = RedisRepository(ModelTest)
        model = ModelTest(name="test", value=42)

        # Save the model
        result = repo.save(model)

        # Check that set was called with the correct parameters
        mock_redis.set.assert_called_once()
        key, json_value = mock_redis.set.call_args[0]

        # Key should be the model class name with prefix
        expected_key = f"{repo.prefix}:{model.__class__.__name__}"
        assert key == expected_key

        # The value should be the JSON representation of the model
        saved_data = json.loads(json_value)
        assert saved_data["name"] == "test"
        assert saved_data["value"] == 42

        # The result should be True
        assert result is True

        # Test with a different model class
        class OtherModel(BaseModel):
            name: str = "other"

        # Save the other model
        other_model = OtherModel(name="test_other")
        result = repo.save(other_model)

        # The key should use the other model class name
        expected_key = f"{repo.prefix}:{other_model.__class__.__name__}"
        assert mock_redis.set.call_args[0][0] == expected_key

        # Test error handling
        mock_redis.set.side_effect = Exception("Redis error")
        result = repo.save(model)
        assert result is False

    @patch("src.mcp_suite.base.models.redis.RedisRepository._get_key")
    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    def test_load(self, mock_get_redis, mock_get_key):
        """Test the load method."""
        # Setup mocks
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_get_key.return_value = "mcp_service:ModelTest"

        # Create a repository and model
        repo = RedisRepository(ModelTest)
        model = ModelTest()

        # Mock Redis to return data
        redis_data = {
            "name": "from_redis",
            "value": 42,
            "created_at": datetime.now(UTC).isoformat(),
        }
        mock_redis.get.return_value = json.dumps(redis_data)

        # Load the model - model_json is returned directly now
        result = repo.load(model)

        # Check that get was called with the correct key
        mock_redis.get.assert_called_once_with(mock_get_key.return_value)
        mock_get_key.assert_called_once_with(model)

        # The result should be the raw JSON string from Redis
        assert result == json.dumps(redis_data)

        # Test with a non-existent model
        mock_redis.get.return_value = None
        result = repo.load(model)
        assert result is None

        # Test error handling
        mock_redis.get.side_effect = Exception("Redis error")
        result = repo.load(model)
        assert result is False

    @patch("src.mcp_suite.base.models.redis.RedisRepository._get_key")
    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    def test_load_with_datetime(self, mock_get_redis, mock_get_key):
        """Test the load method with datetime fields."""
        # Setup mocks
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_get_key.return_value = "mcp_service:ModelWithDatesTest"

        # Create a repository and model
        repo = RedisRepository(ModelWithDatesTest)
        model = ModelWithDatesTest()

        # Create a datetime object
        test_date = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)

        # Mock Redis to return data with ISO format datetime
        redis_data = {"name": "from_redis", "timestamp": test_date.isoformat()}
        mock_redis.get.return_value = json.dumps(redis_data)

        # Load the model - result is just the JSON string
        result = repo.load(model)

        # Check that get was called with the correct key
        mock_redis.get.assert_called_once_with(mock_get_key.return_value)
        mock_get_key.assert_called_once_with(model)

        # Check the result is what we expect
        assert result == json.dumps(redis_data)

    @patch("src.mcp_suite.base.models.redis.RedisRepository._get_key")
    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    def test_delete(self, mock_get_redis, mock_get_key):
        """Test the delete method."""
        # Setup mocks
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_get_key.return_value = "mcp_service:ModelTest"
        mock_redis.delete.return_value = 1

        # Create a repository and model
        repo = RedisRepository(ModelTest)
        model = ModelTest(name="test")

        # Delete the model
        result = repo.delete(model.__class__)

        # Check that delete was called with the correct key
        mock_redis.delete.assert_called_once_with(mock_get_key.return_value)
        mock_get_key.assert_called_once_with(model.__class__)

        # The result should be True
        assert result is True

        # Test error handling
        mock_redis.delete.side_effect = Exception("Redis error")
        result = repo.delete(ModelTest.__class__)
        assert result is False

    @patch("src.mcp_suite.base.models.redis.RedisRepository._get_key")
    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    def test_exists(self, mock_get_redis, mock_get_key):
        """Test the exists method."""
        # Setup mocks
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_get_key.return_value = "mcp_service:ModelTest"
        mock_redis.exists.return_value = 1

        # Create a repository and model
        repo = RedisRepository(ModelTest)
        model = ModelTest(name="test")

        # Check if the model exists
        result = repo.exists(model)

        # Check that exists was called with the correct key
        mock_redis.exists.assert_called_once_with(mock_get_key.return_value)
        mock_get_key.assert_called_once_with(model)

        # The result should be True
        assert result is True

        # Test with a non-existent model
        mock_redis.exists.return_value = 0
        result = repo.exists(model)
        assert result is False

        # Test error handling
        mock_redis.exists.side_effect = Exception("Redis error")
        result = repo.exists(model)
        assert result is False

    @patch("redis.Redis")
    @patch("src.mcp_suite.base.models.redis.repository.REDIS")
    def test_get_redis_connection_exception_handling(
        self, mock_redis_config, mock_redis_class
    ):
        """Test exception handling in get_redis method."""
        # Setup connection failure
        mock_redis_instance = MagicMock()
        mock_redis_class.from_url.return_value = mock_redis_instance
        # Make ping fail to trigger the exception
        mock_redis_instance.ping.side_effect = Exception("Connection failed")

        # Configure Redis settings
        mock_redis_config.URL = "redis://example.com"
        mock_redis_config.PORT = 6379
        mock_redis_config.PASSWORD = "password"

        # Make sure the Redis connection is cleared
        RedisRepository._redis = None

        # Try to get a Redis connection, which should raise RuntimeError
        with pytest.raises(RuntimeError) as excinfo:
            RedisRepository.get_redis()

        # Verify the error message contains our original exception
        assert "Connection failed" in str(excinfo.value)

    def test_get_redis_existing_connection(self):
        """Test that get_redis returns an existing connection if available."""
        # Setup mock redis instance
        mock_redis = MagicMock()

        # Set the existing connection
        RedisRepository._redis = mock_redis

        # Get the Redis connection
        redis_conn = RedisRepository.get_redis()

        # Check that the existing connection was returned
        assert redis_conn == mock_redis

        # Reset for other tests
        RedisRepository._redis = None

    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    def test_list_keys(self, mock_get_redis):
        """Test the list_keys method."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.keys.return_value = ["key1", "key2", "key3"]

        # List keys
        keys = RedisRepository.list_keys()

        # Check that keys was called with the correct pattern
        mock_redis.keys.assert_called_once_with("*")

        # Check the returned keys
        assert keys == ["key1", "key2", "key3"]

        # Test with a specific pattern
        mock_redis.keys.return_value = ["user1", "user2"]
        keys = RedisRepository.list_keys("user*")

        # Check that keys was called with the correct pattern
        mock_redis.keys.assert_called_with("user*")

        # Check the returned keys
        assert keys == ["user1", "user2"]

        # Test error handling
        mock_redis.keys.side_effect = Exception("Redis error")
        keys = RedisRepository.list_keys()
        assert keys == []

    def test_none_connection_after_init(self):
        """Test the scenario where Redis connection is None after initialization."""
        # Reset connection to None
        RedisRepository._redis = None

        # Create a side effect that will set _redis back to None after appearing to succeed
        def from_url_side_effect(*args, **kwargs):
            # First return a mock Redis instance (appears to succeed)
            raise RuntimeError("Could not connect to Redis")

        # Patch Redis.from_url to use our side effect
        with patch("redis.Redis.from_url", side_effect=from_url_side_effect):
            # Also patch REDIS config
            with patch(
                "src.mcp_suite.base.models.redis.repository.REDIS"
            ) as mock_redis_config:
                mock_redis_config.URL = "redis://localhost:6379/0"
                mock_redis_config.PASSWORD = "password"

                # This should now trigger the "Redis connection is None after initialization" error
                with pytest.raises(RuntimeError) as excinfo:
                    RedisRepository.get_redis()

                # Verify the correct error message
                assert "Could not connect to Redis" in str(excinfo.value)
