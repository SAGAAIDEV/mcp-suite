"""Tests for RedisRepository with RedisManager integration."""

from unittest.mock import MagicMock, patch

import redis
from pydantic import BaseModel

from mcp_suite.base.redis.redis_manager import RedisManager
from mcp_suite.base.redis.repository import RedisRepository


class MockModel(BaseModel):
    """Test model for repository tests."""

    name: str
    value: int


@patch("mcp_suite.base.redis.repository.RedisManager")
def test_get_redis_manager(mock_redis_manager_class):
    """Test get_redis_manager method."""
    # Set up mocks
    mock_instance = MagicMock()
    mock_redis_manager_class.return_value = mock_instance

    # Reset class variables
    RedisRepository._redis_manager = None

    # Get redis manager
    redis_manager = RedisRepository.get_redis_manager()

    # Verify correct methods were called
    mock_redis_manager_class.assert_called_once()

    # Verify return value
    assert redis_manager == mock_instance


@patch("redis.Redis.from_url")
def test_get_key_method(mock_from_url):
    """Test the _get_key method of RedisRepository."""
    # Create a repository instance
    repo = RedisRepository(MockModel, prefix="test_prefix")

    # Test the _get_key method
    key = repo._get_key(MockModel)

    # Verify the key format
    assert key.startswith("test_prefix:")
    assert "MockModel" in key


@patch("redis.Redis.from_url")
def test_get_redis_manager_not_running(mock_from_url):
    """Test exception handling when Redis server is not running."""
    # Set up mocks
    mock_redis = MagicMock()
    mock_redis.ping.side_effect = redis.ConnectionError("Connection refused")
    mock_from_url.return_value = mock_redis

    # Reset class variables
    RedisRepository._redis = None
    RedisRepository._redis_manager = None

    # Get redis manager should still work even if Redis is not running
    redis_manager = RedisRepository.get_redis_manager()

    # Verify we got a RedisManager instance
    assert isinstance(redis_manager, RedisManager)


def test_save_model():
    """Test saving a model to Redis."""
    # Create a mock Redis client
    mock_redis = MagicMock()

    # Create repository and model
    repo = RedisRepository(MockModel)
    model = MockModel(name="test", value=123)

    # Mock the get_redis method
    repo.get_redis = MagicMock(return_value=mock_redis)

    try:
        # Save model
        result = repo.save(model)

        # Verify correct methods were called
        mock_redis.set.assert_called_once()

        # Result should be True
        assert result is True
    finally:
        # Remove the mock
        delattr(repo, "get_redis")


def test_close_connection():
    """Test closing the Redis connection."""
    # Create a mock Redis client
    mock_redis = MagicMock()

    # Set the class variable
    RedisRepository._redis = mock_redis

    # Close the connection
    RedisRepository.close_connection()

    # Verify correct methods were called
    mock_redis.close.assert_called_once()
    assert RedisRepository._redis is None


def test_save_model_exception():
    """Test exception handling when saving a model to Redis."""
    # Create a mock Redis client that raises an exception
    mock_redis = MagicMock()
    mock_redis.set.side_effect = Exception("Test exception")

    # Create repository and model
    repo = RedisRepository(MockModel)
    model = MockModel(name="test", value=123)

    # Mock the get_redis method
    repo.get_redis = MagicMock(return_value=mock_redis)

    try:
        # Save model should return False when an exception occurs
        result = repo.save(model)

        # Verify correct methods were called
        mock_redis.set.assert_called_once()

        # Result should be False
        assert result is False
    finally:
        # Remove the mock
        delattr(repo, "get_redis")


def test_load_model():
    """Test loading a model from Redis."""
    # Create a mock Redis client
    mock_redis = MagicMock()
    mock_redis.get.return_value = '{"name": "test", "value": 123}'

    # Create repository and model class
    repo = RedisRepository(MockModel)

    # Mock the get_redis method
    repo.get_redis = MagicMock(return_value=mock_redis)

    try:
        # Load model
        result = repo.load(MockModel)

        # Verify correct methods were called
        mock_redis.get.assert_called_once()

        # Result should be the JSON string
        assert result == '{"name": "test", "value": 123}'
    finally:
        # Remove the mock
        delattr(repo, "get_redis")


def test_load_model_exception():
    """Test exception handling when loading a model from Redis."""
    # Create a mock Redis client that raises an exception
    mock_redis = MagicMock()
    mock_redis.get.side_effect = Exception("Test exception")

    # Create repository and model class
    repo = RedisRepository(MockModel)

    # Mock the get_redis method
    repo.get_redis = MagicMock(return_value=mock_redis)

    try:
        # Load model should return False when an exception occurs
        result = repo.load(MockModel)

        # Verify correct methods were called
        mock_redis.get.assert_called_once()

        # Result should be False
        assert result is False
    finally:
        # Remove the mock
        delattr(repo, "get_redis")


def test_delete_model():
    """Test deleting a model from Redis."""
    # Create a mock Redis client
    mock_redis = MagicMock()

    # Create repository
    repo = RedisRepository(MockModel)

    # Mock the get_redis method
    repo.get_redis = MagicMock(return_value=mock_redis)

    try:
        # Delete model
        result = repo.delete(MockModel)

        # Verify correct methods were called
        mock_redis.delete.assert_called_once()

        # Result should be True
        assert result is True
    finally:
        # Remove the mock
        delattr(repo, "get_redis")


def test_delete_model_exception():
    """Test exception handling when deleting a model from Redis."""
    # Create a mock Redis client that raises an exception
    mock_redis = MagicMock()
    mock_redis.delete.side_effect = Exception("Test exception")

    # Create repository
    repo = RedisRepository(MockModel)

    # Mock the get_redis method
    repo.get_redis = MagicMock(return_value=mock_redis)

    try:
        # Delete model should return False when an exception occurs
        result = repo.delete(MockModel)

        # Verify correct methods were called
        mock_redis.delete.assert_called_once()

        # Result should be False
        assert result is False
    finally:
        # Remove the mock
        delattr(repo, "get_redis")


def test_exists_model():
    """Test checking if a model exists in Redis."""
    # Create a mock Redis client
    mock_redis = MagicMock()
    mock_redis.exists.return_value = 1  # Key exists

    # Create repository
    repo = RedisRepository(MockModel)

    # Mock the get_redis method
    repo.get_redis = MagicMock(return_value=mock_redis)

    try:
        # Check if model exists
        result = repo.exists(MockModel)

        # Verify correct methods were called
        mock_redis.exists.assert_called_once()

        # Result should be True
        assert result is True
    finally:
        # Remove the mock
        delattr(repo, "get_redis")


def test_exists_model_not_found():
    """Test checking if a model exists in Redis when it doesn't."""
    # Create a mock Redis client
    mock_redis = MagicMock()
    mock_redis.exists.return_value = 0  # Key doesn't exist

    # Create repository
    repo = RedisRepository(MockModel)

    # Mock the get_redis method
    repo.get_redis = MagicMock(return_value=mock_redis)

    try:
        # Check if model exists
        result = repo.exists(MockModel)

        # Verify correct methods were called
        mock_redis.exists.assert_called_once()

        # Result should be False
        assert result is False
    finally:
        # Remove the mock
        delattr(repo, "get_redis")


def test_exists_model_exception():
    """Test exception handling when checking if a model exists in Redis."""
    # Create a mock Redis client that raises an exception
    mock_redis = MagicMock()
    mock_redis.exists.side_effect = Exception("Test exception")

    # Create repository
    repo = RedisRepository(MockModel)

    # Mock the get_redis method
    repo.get_redis = MagicMock(return_value=mock_redis)

    try:
        # Check if model exists should return False when an exception occurs
        result = repo.exists(MockModel)

        # Verify correct methods were called
        mock_redis.exists.assert_called_once()

        # Result should be False
        assert result is False
    finally:
        # Remove the mock
        delattr(repo, "get_redis")


def test_list_keys():
    """Test listing keys from Redis."""
    # Create a mock Redis client
    mock_redis = MagicMock()
    mock_redis.keys.return_value = ["key1", "key2", "key3"]

    # Save the original _redis class variable
    original_redis = RedisRepository._redis

    try:
        # Set the _redis class variable
        RedisRepository._redis = mock_redis

        # List keys
        keys = RedisRepository.list_keys("*")

        # Verify correct methods were called
        mock_redis.keys.assert_called_once_with("*")

        # Result should be the list of keys
        assert keys == ["key1", "key2", "key3"]
    finally:
        # Restore the original _redis class variable
        RedisRepository._redis = original_redis


def test_list_keys_exception():
    """Test exception handling when listing keys from Redis."""
    # Create a mock Redis client that raises an exception
    mock_redis = MagicMock()
    mock_redis.keys.side_effect = Exception("Test exception")

    # Save the original _redis class variable
    original_redis = RedisRepository._redis

    try:
        # Set the _redis class variable
        RedisRepository._redis = mock_redis

        # List keys
        keys = RedisRepository.list_keys("*")

        # Result should be an empty list
        assert keys == []
    finally:
        # Restore the original _redis class variable
        RedisRepository._redis = original_redis


def test_get_redis():
    """Test the get_redis method."""
    # Test when _redis is None
    RedisRepository._redis = None

    # Mock the get_redis_manager method
    original_get_redis_manager = RedisRepository.get_redis_manager
    mock_manager = MagicMock()
    mock_client = MagicMock()
    mock_manager.get_client.return_value = mock_client
    RedisRepository.get_redis_manager = classmethod(lambda cls: mock_manager)

    try:
        # Call get_redis
        client = RedisRepository.get_redis()

        # Verify that get_client was called on the manager
        mock_manager.get_client.assert_called_once()

        # Verify that the client is the one returned by the manager
        assert client == mock_client

        # Test when _redis is not None
        mock_redis = MagicMock()
        RedisRepository._redis = mock_redis

        # Call get_redis again
        client = RedisRepository.get_redis()

        # Verify that the client is the one set in _redis
        assert client == mock_redis

        # Verify that get_client was not called again
        assert mock_manager.get_client.call_count == 1
    finally:
        # Restore the original methods and variables
        RedisRepository.get_redis_manager = original_get_redis_manager
        RedisRepository._redis = None
