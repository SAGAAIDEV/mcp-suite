"""
Redis Store Configuration for MCP Suite.

This module provides a Redis store configuration for pydantic-redis models.
"""

import asyncio
from typing import Optional
from urllib.parse import urlparse

from loguru import logger
from pydantic_redis.asyncio import RedisConfig, Store

# Import Redis configuration from env.py
try:
    from config.env import REDIS

    logger.debug(f"Using Redis URL from environment: {REDIS.URL}")
except ImportError:
    logger.warning("Redis configuration not found in config.env, using defaults")
    REDIS = None


def parse_redis_url(url: str) -> dict:
    """
    Parse a Redis URL into connection parameters.

    Args:
        url: Redis URL in the format redis://host:port/db

    Returns:
        Dictionary of connection parameters
    """
    parsed = urlparse(url)

    # Extract host and port
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379

    # Extract database number
    path = parsed.path
    db = int(path.lstrip("/")) if path and path.lstrip("/").isdigit() else 0

    # Extract password if present
    password = parsed.password or None

    return {
        "host": host,
        "port": port,
        "db": db,
        "password": password,
    }


# Global store instance
_store: Optional[Store] = None


def get_redis_store(name: str = "mcp_suite", life_span_in_seconds: int = 86400) -> Store:
    """
    Get the Redis store instance.

    Args:
        name: Name of the store
        life_span_in_seconds: Default TTL for records in seconds

    Returns:
        Redis store instance
    """
    global _store

    if _store is None:
        # Create Redis configuration
        if REDIS:
            # Parse the Redis URL from environment
            conn_params = parse_redis_url(REDIS.URL)
            redis_config = RedisConfig(
                host=conn_params["host"],
                port=conn_params["port"],
                db=conn_params["db"],
                password=conn_params["password"],
            )
        else:
            # Use default configuration
            redis_config = RedisConfig()

        # Create store
        _store = Store(
            name=name,
            redis_config=redis_config,
            life_span_in_seconds=life_span_in_seconds,
        )

        logger.info(
            f"Redis store configured: {redis_config.host}:{redis_config.port} "
            f"(db={redis_config.db})"
        )

    return _store


async def close_redis_store() -> None:
    """Close the Redis store connection."""
    global _store

    if _store is not None:
        # Close the store connection
        await _store.close()
        _store = None
        logger.info("Redis store connection closed")


if __name__ == "__main__":  # pragma: no cover
    # Example usage
    async def main():
        store = get_redis_store()
        logger.info(f"Redis store created: {store}")
        await close_redis_store()

    asyncio.run(main())
