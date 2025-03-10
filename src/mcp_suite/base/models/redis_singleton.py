"""
Redis Singleton Model for MCP Suite.

This module provides a base class for Redis-backed singleton Pydantic models
with explicit Redis persistence methods.
"""

import json
from datetime import UTC, datetime
from typing import Any, ClassVar, Optional, Type, TypeVar

from loguru import logger
from pydantic import Field, field_serializer

from .redis.repository import RedisRepository
from .singleton import Singleton

T = TypeVar("T", bound="RedisSingleton")


class RedisSingleton(Singleton):
    """
    Base model for Redis-backed singleton Pydantic models.

    This class provides explicit Redis persistence methods,
    with the class name as the key. Each model class has exactly one instance
    in memory, making it ideal for service configurations, credentials, etc.

    Unlike the previous implementation, persistence is explicit:
    - Use the save() method to save the model to Redis
    - Use the load() class method to load a model from Redis

    Example:
        ```python
        from mcp_suite.models.redis_singleton import RedisSingleton

        class Credential(RedisSingleton):
            username: str
            password: str

        # Create an instance - explicitly save to Redis
        cred = Credential(username="admin", password="secure123")
        cred.save()

        # Later: Load from Redis explicitly
        cred = Credential.load()
        print(cred.username)  # Prints "admin"

        # Update a field and save explicitly
        cred.username = "new_admin"
        cred.save()
        ```
    """

    # Optional metadata fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Class variables
    _repository: ClassVar[Optional[RedisRepository]] = None
    _is_loading: ClassVar[bool] = False  # Flag to prevent recursive operations

    @field_serializer("*")
    def serialize_all_datetimes(self, v: Any, _info) -> Any:
        """
        Serialize any datetime field to ISO format string for Redis storage.

        This serializer applies to all fields and only transforms datetime objects.
        Other types are returned as-is.
        """
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @classmethod
    def get_repository(cls) -> RedisRepository:
        """Get or create the Redis repository."""
        if cls._repository is None:
            cls._repository = RedisRepository(cls, prefix="0")
        return cls._repository

    def save(self) -> bool:
        """
        Save the model to Redis.

        Updates the updated_at timestamp and persists the model to Redis.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.debug(f"Saving {self.__class__.__name__} to Redis")
            # Update the updated_at timestamp
            self.updated_at = datetime.now(UTC)

            # Use the repository to save the model
            result = self.get_repository().save(self)
            logger.info(f"Saved {self.__class__.__name__} to Redis")
            return result
        except Exception as e:
            logger.error(f"Error saving {self.__class__.__name__} to Redis: {e}")
            return False

    @classmethod
    def load(cls: Type[T]) -> Optional[T]:
        """
        Load the model from Redis.

        Returns:
            Model instance if found in Redis, None otherwise
        """
        # Set the loading flag to prevent recursive operations
        cls._is_loading = True

        try:
            if not cls.exists():
                logger.debug(f"{cls.__name__} not found in Redis")
                return None

            logger.debug(f"Loading {cls.__name__} from Redis")

            # Load data from Redis using the repository
            redis_data = cls.get_repository().load(cls)

            if not redis_data:
                logger.debug(f"No data found for {cls.__name__} in Redis")
                return None

            # Create a new instance with the loaded data using model_validate
            # This properly handles nested objects
            instance = cls(**json.loads(redis_data))
            logger.info(f"Loaded {cls.__name__} data from Redis")
            return instance

        except Exception as e:
            logger.error(f"Error loading {cls.__name__} from Redis: {e}")
            return None
        finally:
            # Reset the loading flag
            cls._is_loading = False

    @classmethod
    def delete(cls) -> bool:
        """
        Delete the model data from Redis.

        This is a class method, so it can be called without an instance:
        MyModel.delete()

        Returns:
            True if successful, False otherwise
        """
        # Use the repository to delete the model
        return cls.get_repository().delete(cls)

    @classmethod
    def exists(cls) -> bool:
        """
        Check if the model exists in Redis.

        Returns:
            True if the model exists, False otherwise
        """
        # Use the repository to check if the model exists
        return cls.get_repository().exists(cls)
