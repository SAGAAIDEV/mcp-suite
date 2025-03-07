"""Redis server management for MCP Suite."""

import subprocess
import time
from typing import Optional, Tuple
from urllib.parse import urlparse

import redis
from loguru import logger

from src.config.env import REDIS
from src.mcp_suite.redis.utils import (
    get_db_dir,
)


def parse_redis_url(url: str) -> Tuple[str, int, Optional[str]]:
    """Parse Redis URL into host, port, and password.

    Args:
        url: Redis URL string

    Returns:
        Tuple[str, int, Optional[str]]: Host, port, and password
    """
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    password = parsed.password
    return host, port, password


def launch_redis_server(
    port: Optional[int] = None,
    password: Optional[str] = None,
    appendonly: bool = True,
    keyspace_events: str = "KEA",
) -> Tuple[bool, Optional[subprocess.Popen]]:
    """Launch a Redis server if it's not already running.

    Args:
        port: Redis server port. Defaults to value from env config.
        password: Redis server password. Defaults to value from env config.
        appendonly: Enable append-only file persistence. Defaults to True.
        keyspace_events: Keyspace notifications configuration. Defaults to "KEA".

    Returns:
        Tuple[bool, Optional[subprocess.Popen]]: Success status and process handle
    """
    global redis_process, redis_launched_by_us

    # Parse Redis URL from environment config
    host, redis_port, redis_password = parse_redis_url(REDIS.URL)

    # Use provided values if specified, otherwise use values from config
    port = port or redis_port
    password = password or redis_password or "redispassword"

    # Check if Redis is already running on the specified port
    try:
        client = redis.Redis(
            host=host, port=port, password=password, socket_connect_timeout=1
        )
        client.ping()
        logger.info(f"Redis server already running on port {port}")
        client.close()
        redis_launched_by_us = False  # We didn't launch it
        return True, None
    except (redis.ConnectionError, redis.ResponseError):
        logger.info(f"No Redis server found on port {port}, launching new instance")

    # Prepare Redis server command
    cmd = [
        "redis-server",
        "--port",
        str(port),
        "--requirepass",
        password,
    ]

    if appendonly:
        cmd.extend(["--appendonly", "yes"])

    if keyspace_events:
        cmd.extend(["--notify-keyspace-events", keyspace_events])

    # Set working directory to the data directory
    db_dir = get_db_dir()
    cmd.extend(["--dir", str(db_dir)])

    try:
        # Launch Redis server as a subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Store the process globally
        redis_process = process

        # Give Redis time to start
        time.sleep(2)

        # Check if process is still running
        if process.poll() is None:
            logger.success(f"Successfully launched Redis server on port {port}")
            logger.info(f"Redis database files will be stored in {db_dir}")
            redis_launched_by_us = True  # We launched it
            return True, process
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Redis server failed to start: {stderr}")
            redis_process = None
            redis_launched_by_us = False
            return False, None
    except Exception as e:
        logger.error(f"Failed to launch Redis server: {e}")
        redis_launched_by_us = False
        return False, None


def shutdown_redis_server():
    """Shutdown the Redis server if it was launched by us."""
    global redis_process, redis_launched_by_us

    # Import here to avoid circular imports
    from src.mcp_suite.redis.client import redis_client

    # Shutdown Redis server ONLY if we started it
    if redis_launched_by_us and redis_process is not None:
        try:
            logger.info("Shutting down Redis server that we launched")
            # Try graceful shutdown first using redis-cli
            if redis_client is not None:
                try:
                    redis_client.shutdown(save=True)
                except Exception as e:
                    logger.warning(f"Could not shutdown Redis via client: {e}")

            # Check if process is still running
            if redis_process.poll() is None:
                logger.info("Terminating Redis server process")
                redis_process.terminate()
                # Give it some time to terminate gracefully
                time.sleep(1)

                # Force kill if still running
                if redis_process.poll() is None:
                    logger.warning(
                        "Redis server not responding to terminate, forcing kill"
                    )
                    redis_process.kill()

            logger.success("Redis server shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down Redis server: {e}")

        # Reset the global variables
        redis_process = None
        redis_launched_by_us = False
