"""Core module for MCP Suite."""

from urllib.parse import urlparse

from loguru import logger

from mcp_suite.base.redis.utils import configure_logger, setup_directories
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


def main() -> str:
    """Run the main function.

    Returns:
        str: A greeting message
    """
    # Set up directories and configure logger
    setup_directories()
    configure_logger()

    logger.info("Starting MCP Suite")

    # Parse Redis URL from environment config
    host, port, password, db = parse_redis_url(REDIS.URL)

    # Launch Redis server if it doesn't exist - REMOVED
    # success, process = launch_redis_server(
    #     port=port, password=password, appendonly=True, keyspace_events="KEA"
    # )

    # if not success:
    #     logger.warning("Could not launch Redis server, attempting to connect anyway")

    # Connect to Redis with the specified configuration - REMOVED
    # redis_client = connect_to_redis(host=host, port=port, password=password, db=db)

    # Simplified version without Redis connection
    logger.info("Redis functionality has been removed or restructured")
    return "Hello from mcp-suite! (Redis functionality has been restructured)"

    # if redis_client:
    #     # Store a test value
    #     redis_client.set("mcp_suite_test", "Hello from Redis!")
    #     # Retrieve the test value
    #     redis_value = redis_client.get("mcp_suite_test")
    #     logger.info(f"Successfully retrieved test value from Redis: {redis_value}")

    #     # For tests, just return a simple message

    #     # For normal operation, include Redis test info
    #     return f"Hello from mcp-suite! Redis test: {redis_value}"
    # else:
    #     logger.error("Redis connection failed")

    #     # For normal operation, include Redis failure info
    #     return "Hello from mcp-suite! (Redis connection failed)"
