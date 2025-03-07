"""
Redis Model for MCP Suite.

This module provides a base class for Redis-backed Pydantic models.

Example:
    ```python
    from mcp_suite.models import RedisModel

    # Create a custom model
    class User(RedisModel):
        email: str
        is_active: bool = True

    # Create and save an instance
    user = User(name="Test User", email="test@example.com")
    await user.save_to_redis()

    # Load the instance from Redis
    loaded_user = await User.load_from_redis(user.id)
    print(loaded_user)
    ```
"""

import asyncio
from datetime import UTC, datetime
from typing import Any, ClassVar, List, Optional, Type, TypeVar, Union
from uuid import UUID, uuid4

from loguru import logger
from pydantic import ConfigDict, Field, field_serializer, model_validator
from pydantic_redis.asyncio import Model as PydanticRedisModel

from mcp_suite.models.redis_store import get_redis_store

T = TypeVar("T", bound="RedisModel")


class RedisModel(PydanticRedisModel):
    """
    Base model for Redis-backed Pydantic models.

    This class extends PydanticRedisModel with additional functionality
    for error handling and convenience methods.

    Attributes:
        id: Unique identifier for the model instance
        name: Human-readable name for the model instance
        description: Optional description of the model instance
        created_at: Timestamp when the model was created
        updated_at: Timestamp when the model was last updated
    """

    # Standard metadata fields
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(...)
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Class variables for Redis configuration
    _primary_key_field: ClassVar[str] = "id"
    _store_registered: ClassVar[bool] = False

    # Pydantic configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="ignore",
    )

    @field_serializer("id")
    def serialize_id(self, id: UUID) -> str:
        """Serialize UUID to string for Redis storage."""
        return str(id)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime to ISO format string for Redis storage."""
        return dt.isoformat()

    @model_validator(mode="before")
    @classmethod
    def ensure_store_registered(cls, data: Any) -> Any:
        """Ensure the model is registered with the Redis store."""
        if not cls._store_registered:
            store = get_redis_store()
            store.register_model(cls)
            cls._store_registered = True
            logger.debug(f"Registered {cls.__name__} with Redis store")
        return data

    async def save_to_redis(self) -> bool:
        """
        Save the model to Redis with error handling.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update the updated_at timestamp
            self.updated_at = datetime.now(UTC)

            # Use the insert method to save to Redis
            await self.__class__.insert(self)

            logger.info(f"Saved {self.__class__.__name__} to Redis: {self.id}")
            return True
        except Exception as e:
            logger.error(f"Error while saving {self.__class__.__name__} to Redis: {e}")
            return False

    @classmethod
    async def load_from_redis(cls: Type[T], id: Union[UUID, str]) -> Optional[T]:
        """
        Load a model from Redis by ID with error handling.

        Args:
            id: UUID of the model to load

        Returns:
            Model instance if found, None otherwise
        """
        try:
            # Convert UUID to string if needed
            id_str = str(id)

            # Use the select method to load from Redis
            results = await cls.select(ids=[id_str])

            if results and len(results) > 0:
                instance = results[0]
                logger.info(f"Loaded {cls.__name__} from Redis: {id}")
                return instance
            else:
                logger.debug(f"{cls.__name__} not found in Redis: {id}")
                return None
        except Exception as e:
            logger.error(f"Error while loading {cls.__name__} from Redis: {e}")
            return None

    async def delete_from_redis(self) -> bool:
        """
        Delete the model from Redis with error handling.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use the delete method to remove from Redis
            id_str = str(self.id)
            await self.__class__.delete(ids=[id_str])

            logger.info(f"Deleted {self.__class__.__name__} from Redis: {self.id}")
            return True
        except Exception as e:
            logger.error(
                f"Error while deleting {self.__class__.__name__} from Redis: {e}"
            )
            return False

    @classmethod
    async def exists_in_redis(cls, id: Union[UUID, str]) -> bool:
        """
        Check if a model exists in Redis with error handling.

        Args:
            id: UUID of the model to check

        Returns:
            True if the model exists, False otherwise
        """
        try:
            # Convert UUID to string if needed
            id_str = str(id)

            # Use the select method to check existence
            results = await cls.select(ids=[id_str])
            return bool(results and len(results) > 0)
        except Exception as e:
            logger.error(f"Error while checking existence in Redis: {e}")
            return False

    @classmethod
    async def get_all_from_redis(cls: Type[T]) -> List[T]:
        """
        Get all instances of this model from Redis.

        Returns:
            List of model instances
        """
        try:
            # Use the select method without IDs to get all instances
            results = await cls.select()

            if results:
                logger.info(
                    f"Loaded {len(results)} {cls.__name__} instances from Redis"
                )
                return results
            else:
                logger.debug(f"No {cls.__name__} instances found in Redis")
                return []
        except Exception as e:
            logger.error(
                f"Error while loading all {cls.__name__} instances from Redis: {e}"
            )
            return []


if __name__ == "__main__":  # pragma: no cover
    # Example usage
    async def main():
        # Create a custom model
        class User(RedisModel):
            email: str
            is_active: bool = True

        # Create and save an instance
        user = User(name="Test User", email="test@example.com")
        await user.save_to_redis()

        # Load the instance from Redis
        loaded_user = await User.load_from_redis(user.id)
        print(loaded_user)

        # Delete the instance
        if loaded_user:
            await loaded_user.delete_from_redis()

    asyncio.run(main())
