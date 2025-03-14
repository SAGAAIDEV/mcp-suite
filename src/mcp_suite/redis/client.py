"""Redis client module for MCP Suite."""

import re
import logging
from typing import Optional, Tuple

import redis
from src.config.env import REDIS

# Initialize global Redis client
redis_client = None

def parse_redis_url(url: str) -> Tuple[str, int, Optional[str], int]:
    """Parse Redis URL into components.

    Args:
        url: Redis URL in format redis://[:password@]host[:port][/db]

    Returns:
        Tuple containing host, port, password, and database number
    """
    # Handle database identifier with regex that accepts only digits
    db_pattern = r"/(\d+)$"
    db_match = re.search(db_pattern, url)

    # Extract and remove the database part if it exists
    db = 0
    if db_match:
        try:
            db = int(db_match.group(1))
            url = url[:db_match.start()]
        except (ValueError, TypeError):
            pass

    # Handle the rest of the URL
    pattern = r"redis://(?::([^@]*)@)?([^:/]+)(?::(\d+))?"
    match = re.match(pattern, url)

    if not match:
        return "localhost", 6379, None, 0

    password, host, port_str = match.groups()

    port = int(port_str) if port_str else 6379

    return host, port, password, db

def connect_to_redis(
    host: Optional[str] = None,
    port: Optional[int] = None,
    password: Optional[str] = None,
    db: Optional[int] = None,
    url: Optional[str] = None,
) -> Optional[redis.Redis]:
    """Connect to Redis server.

    Args:
        host: Redis host, defaults to value from config
        port: Redis port, defaults to value from config
        password: Redis password, defaults to value from config
        db: Redis database number, defaults to 0
        url: Redis URL, overrides other parameters if provided

    Returns:
        Redis client instance or None if connection fails
    """
    global redis_client

    try:
        if url is None and hasattr(REDIS, 'URL'):
            url = REDIS.URL

        # If explicit parameters are passed, use them directly
        if not all([host, port, password is not None, db is not None]) and url:
            parsed_host, parsed_port, parsed_password, parsed_db = parse_redis_url(url)
            host = host or parsed_host
            port = port or parsed_port
            # Only use parsed password if password wasn't explicitly set
            if password is None:
                password = parsed_password
            # Only use parsed db if db wasn't explicitly set
            if db is None:
                db = parsed_db

        # Create Redis client with the parameters
        redis_client = redis.Redis(
            host=host or "localhost",
            port=port or 6379,
            password=password,
            db=db or 0,
            decode_responses=True,
        )

        # Test connection
        redis_client.ping()
        logging.info(f"Connected to Redis at {host}:{port}")
        return redis_client

    except Exception as e:
        logging.error(f"Failed to connect to Redis: {str(e)}")
        redis_client = None
        return None

def close_redis_connection() -> None:
    """Close the Redis connection if it exists."""
    global redis_client

    try:
        if redis_client is not None:
            redis_client.close()
            logging.info("Redis connection closed")
    except Exception as e:
        logging.error(f"Error closing Redis connection: {str(e)}")
