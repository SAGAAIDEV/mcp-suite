"""Signal handling and cleanup for Redis."""

import atexit
import signal
import sys

from loguru import logger

from src.mcp_suite.redis.client import close_redis_connection
from src.mcp_suite.redis.server import shutdown_redis_server
from src.mcp_suite.redis.utils import cleanup_logger


def cleanup():
    """Clean up resources before exiting."""
    # Close Redis client connection
    close_redis_connection()

    # Shutdown Redis server if we launched it
    shutdown_redis_server()

    # Clean up logger handlers
    cleanup_logger()


def signal_handler(sig, frame):
    """Handle termination signals.

    Args:
        sig: Signal number
        frame: Current stack frame
    """
    logger.info(f"Received signal {sig}, shutting down")
    cleanup()
    sys.exit(0)


def register_cleanup_handlers():
    """Register cleanup handlers for graceful shutdown."""
    # Register cleanup function to run on exit
    atexit.register(cleanup)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
