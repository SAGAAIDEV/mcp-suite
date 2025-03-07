"""Redis client management for MCP Suite."""

from typing import Optional
from urllib.parse import urlparse

import redis
from loguru import logger

from src.config.env import REDIS


def parse_redis_url(url: str) -> tuple:
    """Parse Redis URL into connection parameters.

    Args:
        url: Redis URL string

    Returns:
        tuple: Host, port, password, and db number
    """
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    password = parsed.password

    # Extract DB number from path
    path = parsed.path
    db = 0
    if path and len(path) > 1:
        try:
            db = int(path[1:])
        except ValueError:
            logger.warning(f"Invalid DB number in Redis URL: {path[1:]}, using 0")

    return host, port, password, db


def connect_to_redis(
    host: Optional[str] = None,
    port: Optional[int] = None,
    password: Optional[str] = None,
    db: Optional[int] = None,
) -> Optional[redis.Redis]:
    """Connect to a Redis server.

    Args:
        host: Redis server hostname. Defaults to value from env config.
        port: Redis server port. Defaults to value from env config.
        password: Redis server password. Defaults to value from env config.
        db: Redis database number. Defaults to value from env config.

    Returns:
        Optional[redis.Redis]: Redis client instance or None if connection fails
    """
    global redis_client

    # Parse Redis URL from environment config
    redis_host, redis_port, redis_password, redis_db = parse_redis_url(REDIS.URL)

    # Use provided values if specified, otherwise use values from config
    host = host or redis_host
    port = port or redis_port
    password = password or redis_password or "redispassword"
    db = db if db is not None else redis_db

    try:
        client = redis.Redis(
            host=host, port=port, password=password, db=db, decode_responses=True
        )
        # Test the connection
        client.ping()
        logger.info(f"Successfully connected to Redis at {host}:{port}")
        redis_client = client
        return client
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None


def close_redis_connection():
    """Close the Redis client connection if it exists."""
    global redis_client

    if redis_client is not None:
        try:
            logger.info("Closing Redis client connection")
            redis_client.close()
            redis_client = None
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}")
