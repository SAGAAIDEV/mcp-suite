"""
Tests for the RedisModel class.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from mcp_suite.models.redis_model import RedisModel


# Sample model class for testing
class UserModel(RedisModel):
    """Sample user model for testing RedisModel."""

    email: str
    is_active: bool = True


@pytest.fixture
def user_data():
    """Fixture for user test data."""
    return {
        "id": str(uuid4()),
        "name": "Test User",
        "description": "A test user",
        "email": "test@example.com",
        "is_active": True,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }


@pytest.fixture
def user_instance(user_data):
    """Fixture for a UserModel instance."""
    return UserModel(**user_data)


class TestRedisModel:
    """Tests for the RedisModel class."""

    @pytest.mark.asyncio
    @patch("mcp_suite.models.redis_model.get_redis_store")
    async def test_ensure_store_registered(self, mock_get_store):
        """Test that the model is registered with the Redis store."""
        # Setup mock
        mock_store = MagicMock()
        mock_get_store.return_value = mock_store

        # Reset the class variable
        UserModel._store_registered = False

        # Create an instance to trigger registration
        # The model_validator is triggered during validation
        UserModel.model_validate({"name": "Test User", "email": "test@example.com"})

        # Verify store registration
        mock_get_store.assert_called_once()
        mock_store.register_model.assert_called_once_with(UserModel)
        assert UserModel._store_registered is True

    @pytest.mark.asyncio
    @patch.object(UserModel, "insert")
    async def test_save_to_redis_success(self, mock_insert, user_instance):
        """Test saving a model to Redis successfully."""
        # Setup mock
        mock_insert.return_value = None

        # Call method
        result = await user_instance.save_to_redis()

        # Verify result
        assert result is True
        mock_insert.assert_called_once_with(user_instance)

        # Verify updated_at was updated
        assert user_instance.updated_at is not None

    @pytest.mark.asyncio
    @patch.object(UserModel, "insert")
    async def test_save_to_redis_failure(self, mock_insert, user_instance):
        """Test handling errors when saving a model to Redis."""
        # Setup mock to raise an exception
        mock_insert.side_effect = Exception("Test error")

        # Call method
        result = await user_instance.save_to_redis()

        # Verify result
        assert result is False
        mock_insert.assert_called_once_with(user_instance)

    @pytest.mark.asyncio
    @patch.object(UserModel, "select")
    async def test_load_from_redis_success(self, mock_select, user_data):
        """Test loading a model from Redis successfully."""
        # Setup mock
        user_id = user_data["id"]
        user_instance = UserModel(**user_data)
        mock_select.return_value = [user_instance]

        # Call method
        result = await UserModel.load_from_redis(user_id)

        # Verify result
        assert result is user_instance
        mock_select.assert_called_once_with(ids=[user_id])

    @pytest.mark.asyncio
    @patch.object(UserModel, "select")
    async def test_load_from_redis_not_found(self, mock_select):
        """Test handling when a model is not found in Redis."""
        # Setup mock
        user_id = str(uuid4())
        mock_select.return_value = []

        # Call method
        result = await UserModel.load_from_redis(user_id)

        # Verify result
        assert result is None
        mock_select.assert_called_once_with(ids=[user_id])

    @pytest.mark.asyncio
    @patch.object(UserModel, "select")
    async def test_load_from_redis_with_uuid(self, mock_select, user_data):
        """Test loading a model from Redis with a UUID object."""
        # Setup mock
        user_id = UUID(user_data["id"])
        user_instance = UserModel(**user_data)
        mock_select.return_value = [user_instance]

        # Call method
        result = await UserModel.load_from_redis(user_id)

        # Verify result
        assert result is user_instance
        mock_select.assert_called_once_with(ids=[str(user_id)])

    @pytest.mark.asyncio
    @patch.object(UserModel, "select")
    async def test_load_from_redis_error(self, mock_select):
        """Test handling errors when loading a model from Redis."""
        # Setup mock
        user_id = str(uuid4())
        mock_select.side_effect = Exception("Test error")

        # Call method
        result = await UserModel.load_from_redis(user_id)

        # Verify result
        assert result is None
        mock_select.assert_called_once_with(ids=[user_id])

    @pytest.mark.asyncio
    @patch.object(UserModel, "delete")
    async def test_delete_from_redis_success(self, mock_delete, user_instance):
        """Test deleting a model from Redis successfully."""
        # Setup mock
        mock_delete.return_value = None

        # Call method
        result = await user_instance.delete_from_redis()

        # Verify result
        assert result is True
        mock_delete.assert_called_once_with(ids=[str(user_instance.id)])

    @pytest.mark.asyncio
    @patch.object(UserModel, "delete")
    async def test_delete_from_redis_error(self, mock_delete, user_instance):
        """Test handling errors when deleting a model from Redis."""
        # Setup mock
        mock_delete.side_effect = Exception("Test error")

        # Call method
        result = await user_instance.delete_from_redis()

        # Verify result
        assert result is False
        mock_delete.assert_called_once_with(ids=[str(user_instance.id)])

    @pytest.mark.asyncio
    @patch.object(UserModel, "select")
    async def test_exists_in_redis_true(self, mock_select):
        """Test checking if a model exists in Redis (exists)."""
        # Setup mock
        user_id = str(uuid4())
        mock_select.return_value = [MagicMock()]

        # Call method
        result = await UserModel.exists_in_redis(user_id)

        # Verify result
        assert result is True
        mock_select.assert_called_once_with(ids=[user_id])

    @pytest.mark.asyncio
    @patch.object(UserModel, "select")
    async def test_exists_in_redis_false(self, mock_select):
        """Test checking if a model exists in Redis (does not exist)."""
        # Setup mock
        user_id = str(uuid4())
        mock_select.return_value = []

        # Call method
        result = await UserModel.exists_in_redis(user_id)

        # Verify result
        assert result is False
        mock_select.assert_called_once_with(ids=[user_id])

    @pytest.mark.asyncio
    @patch.object(UserModel, "select")
    async def test_exists_in_redis_error(self, mock_select):
        """Test handling errors when checking if a model exists in Redis."""
        # Setup mock
        user_id = str(uuid4())
        mock_select.side_effect = Exception("Test error")

        # Call method
        result = await UserModel.exists_in_redis(user_id)

        # Verify result
        assert result is False
        mock_select.assert_called_once_with(ids=[user_id])

    @pytest.mark.asyncio
    @patch.object(UserModel, "select")
    async def test_get_all_from_redis_success(self, mock_select, user_data):
        """Test getting all models from Redis successfully."""
        # Setup mock
        user_instances = [UserModel(**user_data) for _ in range(3)]
        mock_select.return_value = user_instances

        # Call method
        result = await UserModel.get_all_from_redis()

        # Verify result
        assert result == user_instances
        mock_select.assert_called_once_with()

    @pytest.mark.asyncio
    @patch.object(UserModel, "select")
    async def test_get_all_from_redis_empty(self, mock_select):
        """Test getting all models from Redis when none exist."""
        # Setup mock
        mock_select.return_value = []

        # Call method
        result = await UserModel.get_all_from_redis()

        # Verify result
        assert result == []
        mock_select.assert_called_once_with()

    @pytest.mark.asyncio
    @patch.object(UserModel, "select")
    async def test_get_all_from_redis_error(self, mock_select):
        """Test handling errors when getting all models from Redis."""
        # Setup mock
        mock_select.side_effect = Exception("Test error")

        # Call method
        result = await UserModel.get_all_from_redis()

        # Verify result
        assert result == []
        mock_select.assert_called_once_with()

    def test_field_serializers(self, user_instance):
        """Test the field serializers."""
        # Test UUID serializer
        uuid_str = user_instance.serialize_id(user_instance.id)
        assert isinstance(uuid_str, str)
        assert uuid_str == str(user_instance.id)

        # Test datetime serializer
        now = datetime.now(UTC)
        dt_str = user_instance.serialize_datetime(now)
        assert isinstance(dt_str, str)
        assert dt_str == now.isoformat()
