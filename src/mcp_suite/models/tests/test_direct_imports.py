"""
Tests for direct imports of modules to ensure coverage.
"""

import pytest


def test_direct_import_redis_model():
    """Test direct import of redis_model module."""
    from src.mcp_suite.models.redis_model import (
        RedisModel,
        T,
        datetime,
        UUID,
        uuid4,
        logger,
        get_redis_store,
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


def test_direct_import_redis_store():
    """Test direct import of redis_store module."""
    from src.mcp_suite.models.redis_store import (
        parse_redis_url,
        get_redis_store,
        close_redis_store,
        logger,
        Store,
        RedisConfig,
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