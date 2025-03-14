"""
Tests for direct imports of modules to ensure coverage.
"""
from unittest.mock import patch


@patch("src.mcp_suite.models.redis_store.Store")
def test_direct_import_redis_model(mock_store):
    """Test direct import of redis_model module."""
    # Mock the get_redis_store function before importing
    with patch("src.mcp_suite.models.redis_store.get_redis_store") as mock_get_store:
        # Set up the mock
        mock_get_store.return_value = mock_store

        from src.mcp_suite.models.redis_model import (
            UUID,
            RedisModel,
            T,
            datetime,
            get_redis_store,
            logger,
            uuid4,
        )

        # Verify imports
        assert RedisModel is not None
        assert T is not None
        assert datetime is not None
        assert UUID is not None
        assert uuid4 is not None
        assert logger is not None
        assert get_redis_store is not None

        # Create a simple model
        class TestModel(RedisModel):
            test_field: str

        # Create an instance
        model = TestModel(name="Test", test_field="value")

        # Test serializers
        assert isinstance(model.serialize_id(model.id), str)
        assert isinstance(model.serialize_datetime(model.created_at), str)


@patch("src.mcp_suite.models.redis_store.REDIS", None)
@patch("src.mcp_suite.models.redis_store.Store")
def test_direct_import_redis_store(mock_store, mock_redis=None):
    """Test direct import of redis_store module."""
    # Configure the mock before import
    mock_store_instance = mock_store.return_value

    # Import after mocking
    from src.mcp_suite.models.redis_store import (
        RedisConfig,
        Store,
        close_redis_store,
        get_redis_store,
        logger,
        parse_redis_url,
    )

    # Verify imports
    assert parse_redis_url is not None
    assert get_redis_store is not None
    assert close_redis_store is not None
    assert logger is not None
    assert Store is not None
    assert RedisConfig is not None

    # Test parse_redis_url
    result = parse_redis_url("redis://localhost:6379/0")
    assert result["host"] == "localhost"
    assert result["port"] == 6379
    assert result["db"] == 0
    assert result["password"] is None
