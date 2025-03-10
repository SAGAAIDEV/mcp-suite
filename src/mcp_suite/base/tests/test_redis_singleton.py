"""
Tests for the RedisSingleton base class.

This module tests the functionality of the RedisSingleton base class.
"""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ConfigDict, Field

from src.mcp_suite.base.models.redis import RedisRepository
from src.mcp_suite.base.models.redis_singleton import RedisSingleton


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset all singleton instances before and after each test."""
    # Clear the _instances dictionary before the test
    RedisSingleton._instances = {}

    # Reset the repository
    RedisSingleton._repository = None

    # Reset the loading flag
    RedisSingleton._is_loading = False

    # Run the test
    yield

    # Clear the dictionaries after the test as well
    RedisSingleton._instances = {}
    RedisSingleton._repository = None
    RedisSingleton._is_loading = False


class TestRedisSingleton:
    """Test cases for the RedisSingleton base class."""

    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.get_redis")
    def test_basic_singleton_behavior(self, mock_get_redis):
        """Test that RedisSingleton maintains basic singleton behavior."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Define a test redis singleton class
        class TestConfig(RedisSingleton):
            name: str = "default"
            value: int = 0
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Create first instance
        config1 = TestConfig(name="test", value=42)

        # Create second instance
        config2 = TestConfig()

        # They should be the same object
        assert config1 is config2

        # The values should be preserved
        assert config2.name == "test"
        assert config2.value == 42

    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.get_redis")
    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.save")
    def test_explicit_save(self, mock_save, mock_get_redis):
        """Test that model is saved to Redis via explicit save() method."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Make save method store the model for inspection
        saved_model = None

        def save_side_effect(model):
            nonlocal saved_model
            saved_model = model
            return True

        mock_save.side_effect = save_side_effect

        # Define a test redis singleton class
        class TestSettings(RedisSingleton):
            name: str = "default"
            timeout: int = 30
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Create an instance
        settings = TestSettings(name="test", timeout=60)

        # Initially, save should not have been called
        mock_save.assert_not_called()

        # Now explicitly save the model
        result = settings.save()

        # Verify that save was called
        mock_save.assert_called_once()

        # Verify the save method returned True
        assert result is True

        # Verify the saved model has the correct values
        assert saved_model is not None
        assert saved_model.name == "test"
        assert saved_model.timeout == 60

    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.get_redis")
    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.load")
    def test_explicit_load(self, mock_load, mock_get_redis):
        """Test that model is loaded from Redis via explicit load() class method."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Define a test redis singleton class
        class TestCredential(RedisSingleton):
            username: str = ""
            password: str = ""
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Mock Redis to return data
        redis_data = {
            "username": "admin",
            "password": "secure123",
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        mock_redis.exists.return_value = True

        # Configure the mock_load to return JSON data
        mock_load.return_value = json.dumps(redis_data)

        # Load the model using the explicit load method
        credential = TestCredential.load()

        # Verify that load method was called
        mock_load.assert_called_once()

        # The model should have the values from Redis
        assert credential.username == "admin"
        assert credential.password == "secure123"

    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.get_redis")
    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.load")
    def test_load_returns_none_when_not_exists(self, mock_load, mock_get_redis):
        """Test that load() returns None when model doesn't exist in Redis."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Define a test redis singleton class
        class TestCredential(RedisSingleton):
            username: str = ""
            password: str = ""
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Mock Redis to indicate model doesn't exist
        mock_redis.exists.return_value = False
        mock_load.return_value = None

        # Load the model
        credential = TestCredential.load()

        # The load method should return None since model doesn't exist
        assert credential is None

        # Verify that exists was called but load wasn't - it short-circuits
        mock_redis.exists.assert_called_once()
        mock_load.assert_not_called()

    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.get_redis")
    def test_delete_from_redis(self, mock_get_redis):
        """Test that model can be deleted from Redis."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.delete.return_value = 1

        # Define a test redis singleton class
        class TestCache(RedisSingleton):
            size: int = 100
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Delete the model
        result = TestCache.delete()

        # Verify that delete was called on Redis
        mock_redis.delete.assert_called_once()

        # The result should be True
        assert result is True

    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.get_redis")
    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    def test_exists_in_redis(self, mock_get_redis2, mock_get_redis):
        """Test that model existence can be checked in Redis."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.exists.return_value = True

        # Define a test redis singleton class
        class TestCache(RedisSingleton):
            size: int = 100
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Check if the model exists
        result = TestCache.exists()

        # Verify that exists was called on Redis
        mock_redis.exists.assert_called_once()

        # The result should be True
        assert result is True

    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    def test_datetime_serialization(self, mock_get_redis):
        """Test serialization of datetime fields."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Define a test redis singleton class with a datetime field
        class TestEvent(RedisSingleton):
            name: str = "event"
            timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Create an instance with a datetime
        now = datetime.now(UTC)
        event = TestEvent(name="test", timestamp=now)

        # Save to Redis to trigger serialization
        event.save()

        # Check that the timestamp is serialized to an ISO 8601 string
        assert isinstance(event.model_dump()["timestamp"], str)

        # Ensure the timestamp string conforms to ISO 8601 format
        try:
            datetime.fromisoformat(event.model_dump()["timestamp"])
            is_valid_iso = True
        except ValueError:
            is_valid_iso = False

        assert is_valid_iso, "Timestamp was not serialized to a valid ISO 8601 format"

    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    def test_multiple_redis_singleton_classes(self, mock_get_redis):
        """Test that multiple RedisSingleton classes can coexist."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Define two different redis singleton classes
        class TestConfigA(RedisSingleton):
            value: str = "A"
            model_config = ConfigDict(arbitrary_types_allowed=True)

        class TestConfigB(RedisSingleton):
            value: str = "B"
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Create instances of both classes
        config_a = TestConfigA()
        config_b = TestConfigB()

        # They should be different objects
        assert config_a is not config_b

        # Each should maintain its own value
        assert config_a.value == "A"
        assert config_b.value == "B"

        # Modifying one should not affect the other
        config_a.value = "Modified A"
        assert config_a.value == "Modified A"
        assert config_b.value == "B"

    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    def test_repository_creation(self, mock_get_redis):
        """Test that repository is created only once."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Define a test redis singleton class
        class TestConfig(RedisSingleton):
            name: str = "default"
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Get repository twice
        repo1 = TestConfig.get_repository()
        repo2 = TestConfig.get_repository()

        # They should be the same object
        assert repo1 is repo2

        # The repository should have been created with the correct model class
        assert isinstance(repo1, RedisRepository)
        assert repo1.model_class is TestConfig

    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.load")
    def test_error_handling_during_load(self, mock_load, mock_get_redis):
        """Test error handling during loading from Redis."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Define a test redis singleton class
        class TestConfig(RedisSingleton):
            name: str = "default"
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Mock Redis to indicate model exists but throw exception on load
        mock_redis.exists.return_value = True
        mock_load.side_effect = Exception("Redis connection error")

        # Try to load the model
        result = TestConfig.load()

        # Should return None and not propagate the exception
        assert result is None

    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.save")
    def test_error_handling_during_save(self, mock_save, mock_get_redis):
        """Test error handling during saving to Redis."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Define a test redis singleton class
        class TestConfig(RedisSingleton):
            name: str = "default"
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Mock save to throw exception
        mock_save.side_effect = Exception("Redis connection error")

        # Create an instance
        config = TestConfig(name="test")

        # Try to save the model explicitly
        result = config.save()

        # Should return False and not propagate the exception
        assert result is False

    @patch("src.mcp_suite.base.models.redis.RedisRepository.get_redis")
    def test_serialize_datetime_with_string(self, mock_get_redis):
        """Test serialization of string values in datetime fields."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Define a test redis singleton class with a string field
        # that might contain a datetime string
        class TestEvent(RedisSingleton):
            name: str = "event"
            timestamp: str = "2023-01-01T00:00:00+00:00"
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Create an instance
        event = TestEvent()

        # Save to trigger serialization
        event.save()

        # Check that string fields remain as strings after serialization
        assert isinstance(event.timestamp, str)
        assert event.timestamp == "2023-01-01T00:00:00+00:00"

    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.get_redis")
    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.load")
    def test_load_returns_none_when_data_empty(self, mock_load, mock_get_redis):
        """Test that load() returns None when model exists but has empty data."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Define a test redis singleton class
        class TestCredential(RedisSingleton):
            username: str = ""
            password: str = ""
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Mock Redis to indicate model exists but return empty data
        mock_redis.exists.return_value = True
        mock_load.return_value = None  # Simulate empty data from Redis

        # Load the model
        credential = TestCredential.load()

        # The load method should return None since data is empty
        assert credential is None

        # Verify that exists and load were both called
        mock_redis.exists.assert_called_once()
        mock_load.assert_called_once()

    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.get_redis")
    @patch("src.mcp_suite.base.models.redis_singleton.RedisRepository.load")
    def test_load_handles_invalid_json(self, mock_load, mock_get_redis):
        """Test that load() handles invalid JSON data gracefully."""
        # Setup mock
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Define a test redis singleton class
        class TestCredential(RedisSingleton):
            username: str = ""
            password: str = ""
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Mock Redis to indicate model exists but return invalid JSON
        mock_redis.exists.return_value = True
        mock_load.return_value = "{invalid json data}"  # Simulate invalid JSON

        # Load the model
        credential = TestCredential.load()

        # The load method should return None when it encounters invalid JSON
        assert credential is None

        # Verify that exists and load were both called
        mock_redis.exists.assert_called_once()
        mock_load.assert_called_once()
