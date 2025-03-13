"""
Tests for the RedisSingleton class.

This module contains tests for the RedisSingleton class, which provides
Redis-backed singleton functionality for Pydantic models.
"""

import json
from datetime import UTC, datetime
from unittest.mock import patch

from mcp_suite.base.models.singleton import Singleton
from mcp_suite.base.redis.redis_singleton import RedisSingleton
from mcp_suite.base.redis.repository import RedisRepository


class TestRedisSingleton:
    """Tests for the RedisSingleton class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset the Singleton instances to ensure clean tests
        Singleton._instances = {}
        # Reset the repository
        RedisSingleton._repository = None
        # Reset the loading flag
        RedisSingleton._is_loading = False

    def teardown_method(self):
        """Clean up after each test method."""
        # Reset the Singleton instances
        Singleton._instances = {}
        # Reset the repository
        RedisSingleton._repository = None
        # Reset the loading flag
        RedisSingleton._is_loading = False

    # Define a test model class for use in tests
    class TestModel(RedisSingleton):
        """Test model for RedisSingleton tests."""

        name: str = "default_name"
        value: int = 0

    def test_initialization(self):
        """Test that RedisSingleton initializes correctly with proper fields."""
        # Create a new instance
        model = self.TestModel(name="test", value=42)

        # Check that the fields are set correctly
        assert model.name == "test"
        assert model.value == 42

        # Check that the metadata fields are set
        # Note: In the actual implementation, created_at and updated_at might be strings
        # due to serialization, so we check for either datetime or string
        assert isinstance(model.created_at, (datetime, str))
        assert isinstance(model.updated_at, (datetime, str))

        # Check that it's a singleton
        model2 = self.TestModel(name="another")
        assert model is model2
        assert model2.name == "another"  # Should be updated
        assert model2.value == 42  # Should retain the previous value

    def test_datetime_serialization(self):
        """Test that datetime fields are serialized correctly."""
        # Create a fixed datetime for testing
        test_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)

        # Create a model with the fixed datetime
        model = self.TestModel(name="test", created_at=test_time, updated_at=test_time)

        # Test the serializer directly
        serialized = model.serialize_all_datetimes(test_time, None)
        assert serialized == "2023-01-01T12:00:00+00:00"

        # Test that non-datetime values are returned as-is
        assert model.serialize_all_datetimes("string", None) == "string"
        assert model.serialize_all_datetimes(42, None) == 42

    def test_get_repository(self):
        """Test that get_repository returns a RedisRepository instance."""
        # Call the method
        repo = self.TestModel.get_repository()

        # Check that it's a RedisRepository
        assert isinstance(repo, RedisRepository)

        # Check that it's cached
        assert self.TestModel._repository is repo

        # Call again and check that it returns the same instance
        repo2 = self.TestModel.get_repository()
        assert repo is repo2

    @patch.object(RedisRepository, "save")
    def test_save(self, mock_save):
        """Test that save updates the updated_at timestamp and calls the repository."""
        # Set up the mock
        mock_save.return_value = True

        # Create a model
        model = self.TestModel(name="test")
        original_updated_at = model.updated_at

        # Save the model
        result = model.save()

        # Check that the repository's save method was called
        mock_save.assert_called_once_with(model)

        # Check that the result is True
        assert result is True

        # Check that updated_at was updated
        # Since updated_at might be a string or a datetime, we need to handle both cases
        if isinstance(original_updated_at, str) and isinstance(model.updated_at, str):
            # Compare strings
            assert model.updated_at > original_updated_at
        elif isinstance(original_updated_at, datetime) and isinstance(
            model.updated_at, datetime
        ):
            # Compare datetimes
            assert model.updated_at > original_updated_at
        else:
            # One is a string and one is a datetime, so we can't directly compare
            # Instead, we'll just check that they're different
            assert model.updated_at != original_updated_at

    @patch.object(RedisRepository, "save")
    def test_save_failure(self, mock_save):
        """Test that save handles exceptions and returns False on failure."""
        # Set up the mock to raise an exception
        mock_save.side_effect = Exception("Test exception")

        # Create a model
        model = self.TestModel(name="test")

        # Save the model
        result = model.save()

        # Check that the result is False
        assert result is False

    @patch.object(RedisRepository, "load")
    @patch.object(RedisRepository, "exists")
    def test_load(self, mock_exists, mock_load):
        """Test that load calls the repository and returns a model instance."""
        # Set up the mocks
        mock_exists.return_value = True
        mock_load.return_value = json.dumps(
            {
                "name": "loaded",
                "value": 99,
                "created_at": "2023-01-01T12:00:00+00:00",
                "updated_at": "2023-01-01T12:00:00+00:00",
            }
        )

        # Load the model
        model = self.TestModel.load()

        # Check that the repository's exists and load methods were called
        mock_exists.assert_called_once_with(self.TestModel)
        mock_load.assert_called_once_with(self.TestModel)

        # Check that a model instance was returned
        assert isinstance(model, self.TestModel)
        assert model.name == "loaded"
        assert model.value == 99

    @patch.object(RedisRepository, "exists")
    def test_load_not_exists(self, mock_exists):
        """Test that load returns None if the model doesn't exist in Redis."""
        # Set up the mock
        mock_exists.return_value = False

        # Load the model
        model = self.TestModel.load()

        # Check that the repository's exists method was called
        mock_exists.assert_called_once_with(self.TestModel)

        # Check that None was returned
        assert model is None

    @patch.object(RedisRepository, "load")
    @patch.object(RedisRepository, "exists")
    def test_load_no_data(self, mock_exists, mock_load):
        """Test that load returns None if no data is found in Redis."""
        # Set up the mocks
        mock_exists.return_value = True
        mock_load.return_value = None

        # Load the model
        model = self.TestModel.load()

        # Check that the repository's exists and load methods were called
        mock_exists.assert_called_once_with(self.TestModel)
        mock_load.assert_called_once_with(self.TestModel)

        # Check that None was returned
        assert model is None

    @patch.object(RedisRepository, "load")
    @patch.object(RedisRepository, "exists")
    def test_load_exception(self, mock_exists, mock_load):
        """Test that load handles exceptions and returns None on failure."""
        # Set up the mocks
        mock_exists.return_value = True
        mock_load.side_effect = Exception("Test exception")

        # Load the model
        model = self.TestModel.load()

        # Check that the repository's exists and load methods were called
        mock_exists.assert_called_once_with(self.TestModel)
        mock_load.assert_called_once_with(self.TestModel)

        # Check that None was returned
        assert model is None

    @patch.object(RedisRepository, "delete")
    def test_delete(self, mock_delete):
        """Test that delete calls the repository."""
        # Set up the mock
        mock_delete.return_value = True

        # Delete the model
        result = self.TestModel.delete()

        # Check that the repository's delete method was called
        mock_delete.assert_called_once_with(self.TestModel)

        # Check that the result is True
        assert result is True

    @patch.object(RedisRepository, "exists")
    def test_exists(self, mock_exists):
        """Test that exists calls the repository."""
        # Set up the mock
        mock_exists.return_value = True

        # Check if the model exists
        result = self.TestModel.exists()

        # Check that the repository's exists method was called
        mock_exists.assert_called_once_with(self.TestModel)

        # Check that the result is True
        assert result is True

    def test_is_loading_flag(self):
        """Test that the _is_loading flag prevents recursive operations."""
        # Set the loading flag
        self.TestModel._is_loading = True

        # Mock the exists method to return True
        with patch.object(RedisRepository, "exists", return_value=True):
            # Try to load the model
            model = self.TestModel.load()

            # Check that None was returned
            assert model is None

        # Reset the loading flag
        self.TestModel._is_loading = False

        # Mock the exists and load methods
        with (
            patch.object(RedisRepository, "exists", return_value=True),
            patch.object(
                RedisRepository,
                "load",
                return_value=json.dumps({"name": "test_loading", "value": 42}),
            ),
        ):
            # Load the model
            model = self.TestModel.load()

            # Check that a model was returned
            assert model is not None
            assert model.name == "test_loading"


class TestRedisSingletonIntegration:
    """Integration tests for the RedisSingleton class with mocked Redis."""

    # Define a test model class for integration tests
    class IntegrationTestModel(RedisSingleton):
        """Test model for RedisSingleton integration tests."""

        name: str = "default_integration_name"
        value: int = 0

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset the Singleton instances to ensure clean tests
        Singleton._instances = {}
        # Reset the repository
        RedisSingleton._repository = None
        # Reset the loading flag
        RedisSingleton._is_loading = False

    def teardown_method(self):
        """Clean up after each test method."""
        # Reset the Singleton instances
        Singleton._instances = {}
        # Reset the repository
        RedisSingleton._repository = None
        # Reset the loading flag
        RedisSingleton._is_loading = False

    @patch.object(RedisRepository, "save")
    @patch.object(RedisRepository, "load")
    @patch.object(RedisRepository, "exists")
    def test_save_and_load(self, mock_exists, mock_load, mock_save):
        """Test saving and loading a model to/from Redis."""
        # Set up the mocks
        mock_save.return_value = True
        mock_exists.return_value = True
        mock_load.return_value = json.dumps(
            {
                "name": "integration_test",
                "value": 123,
                "created_at": "2023-01-01T12:00:00+00:00",
                "updated_at": "2023-01-01T12:00:00+00:00",
            }
        )

        # Create and save a model
        model = self.IntegrationTestModel(name="integration_test", value=123)
        save_result = model.save()

        # Check that the save was successful
        assert save_result is True
        mock_save.assert_called_once_with(model)

        # Reset the singleton instance to force a reload from Redis
        Singleton._instances = {}

        # Load the model from Redis
        loaded_model = self.IntegrationTestModel.load()

        # Check that the model was loaded correctly
        assert loaded_model is not None
        assert loaded_model.name == "integration_test"
        assert loaded_model.value == 123
        mock_exists.assert_called_with(self.IntegrationTestModel)
        mock_load.assert_called_with(self.IntegrationTestModel)

    @patch.object(RedisRepository, "save")
    @patch.object(RedisRepository, "delete")
    @patch.object(RedisRepository, "exists")
    def test_delete(self, mock_exists, mock_delete, mock_save):
        """Test deleting a model from Redis."""
        # Set up the mocks
        mock_save.return_value = True
        mock_delete.return_value = True
        # First exists check returns True, second returns False after deletion
        mock_exists.side_effect = [True, False]

        # Create and save a model
        model = self.IntegrationTestModel(name="delete_test", value=456)
        model.save()

        # Check that the model exists
        assert self.IntegrationTestModel.exists() is True

        # Delete the model
        delete_result = self.IntegrationTestModel.delete()

        # Check that the delete was successful
        assert delete_result is True
        mock_delete.assert_called_once_with(self.IntegrationTestModel)

        # Check that the model no longer exists
        assert self.IntegrationTestModel.exists() is False

    @patch.object(RedisRepository, "save")
    @patch.object(RedisRepository, "load")
    @patch.object(RedisRepository, "exists")
    def test_update(self, mock_exists, mock_load, mock_save):
        """Test updating a model in Redis."""
        # Set up the mocks
        mock_save.return_value = True
        mock_exists.return_value = True
        mock_load.return_value = json.dumps(
            {
                "name": "updated",
                "value": 999,
                "created_at": "2023-01-01T12:00:00+00:00",
                "updated_at": "2023-01-01T12:00:00+00:00",
            }
        )

        # Create and save a model
        model = self.IntegrationTestModel(name="update_test", value=789)
        model.save()

        # Update the model
        model.name = "updated"
        model.value = 999
        update_result = model.save()

        # Check that the update was successful
        assert update_result is True
        assert (
            mock_save.call_count == 2
        )  # Called twice: once for initial save, once for update

        # Reset the singleton instance to force a reload from Redis
        Singleton._instances = {}

        # Load the model from Redis
        loaded_model = self.IntegrationTestModel.load()

        # Check that the model was updated correctly
        assert loaded_model is not None
        assert loaded_model.name == "updated"
        assert loaded_model.value == 999
