"""
Redis Repository for MCP Suite.

This module provides a repository class for Redis persistence operations.
"""

from typing import List, Optional, Type

import redis
from loguru import logger
from pydantic import BaseModel

from config.env import REDIS


class RedisRepository:
    """
    Repository for Redis persistence operations.

    This class handles all Redis-related operations for a model,
    including saving, loading, and deleting data.
    """

    _redis: Optional[redis.Redis] = None

    def __init__(self, model_class: Type, prefix: str = "mcp_service"):
        """
        Initialize the repository.

        Args:
            model_class: The model class to use
            prefix: Optional prefix for Redis keys
        """
        self.model_class = model_class
        self.prefix = prefix
        # Save the key on initialization
        self.key = ""

    def _get_key(self, model: Type[BaseModel]) -> str:
        """
        Get the Redis key for a model.

        This method is kept for backward compatibility.
        For the repository's own model class, use self.key instead.

        Args:
            model_name: The name of the model

        Returns:
            The Redis key
        """

        return f"{self.prefix}:{model.__name__}"

    @classmethod
    def get_redis(cls) -> redis.Redis:
        """Get or create the Redis connection."""
        if cls._redis is None:
            try:
                # Parse Redis URL if it's a full URL
                if REDIS.URL.startswith("redis://"):
                    # Use from_url for proper URL parsing
                    cls._redis = redis.Redis.from_url(
                        REDIS.URL,
                        password=REDIS.PASSWORD,
                        decode_responses=True,
                    )
                else:
                    # Create Redis connection with explicit parameters
                    cls._redis = redis.Redis(
                        host=REDIS.URL,
                        port=REDIS.PORT,
                        password=REDIS.PASSWORD,
                        decode_responses=True,
                    )

                # Test the connection
                cls._redis.ping()
                logger.debug(f"Connected to Redis: {REDIS.URL}:{REDIS.PORT}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                # Make sure we don't leave _redis as None which causes NoneType errors
                raise RuntimeError(f"Could not connect to Redis: {e}")

        return cls._redis

    def save(self, model: BaseModel) -> bool:
        """
        Save a model to Redis.

        Args:
            model: The model to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the Redis connection
            r = self.get_redis()

            # Get the key - use the pre-computed key if it's the repository's model class

            key = self._get_key(model.__class__)

            # Serialize the model to JSON
            model_json = model.model_dump_json()
            # Store in Redis
            r.set(key, model_json)

            logger.info(f"Saved {model.__class__.__name__} to Redis")
            return True
        except Exception as e:
            logger.error(f"Error saving {model.__class__.__name__} to Redis: {e}")
            return False

    def load(self, model: Type[BaseModel]) -> bool:
        """
        Load a model from Redis.

        Args:
            model: The model to load data into

        Returns:
            True if data was loaded, False otherwise
        """
        try:
            # Get the Redis connection
            r = self.get_redis()

            model_json = r.get(self._get_key(model))
            return model_json

        except Exception as e:
            logger.error(f"Error loading {model.__class__.__name__} from Redis: {e}")
            return False

    def delete(self, model: Type[BaseModel]) -> bool:
        """
        Delete a model from Redis.

        Args:
            model_name: The name of the model to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the Redis connection
            r = self.get_redis()

            # Get the key - use the pre-computed key if it's the repository's model class
            key = self._get_key(model)

            # Delete from Redis
            r.delete(key)

            logger.info(f"Deleted {model.__name__} from Redis")
            return True
        except Exception as e:
            logger.error(f"Error deleting {model.__name__} from Redis: {e}")
            return False

    def exists(self, model: Type[BaseModel]) -> bool:
        """
        Check if a model exists in Redis.

        Args:
            model_name: The name of the model to check

        Returns:
            True if the model exists, False otherwise
        """
        try:
            # Get the Redis connection
            r = self.get_redis()

            # Get the key - use the pre-computed key if it's the repository's model class
            key = self._get_key(model)

            # Check if the key exists
            return bool(r.exists(key))
        except Exception as e:
            logger.error(
                f"Error checking if {model.__class__.__name__} exists in Redis: {e}"
            )
            return False

    @classmethod
    def list_keys(cls, pattern: str = "*") -> List[str]:
        """
        List all keys in Redis matching a pattern.

        This is useful for debugging to see what keys actually exist.

        Args:
            pattern: The pattern to match keys against

        Returns:
            List of keys matching the pattern
        """
        try:
            r = cls.get_redis()
            keys = r.keys(pattern)
            return keys
        except Exception as e:
            logger.error(f"Error listing keys from Redis: {e}")
            return []
