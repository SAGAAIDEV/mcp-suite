"""Redis utilities for MCP Suite."""

import sys
from pathlib import Path

from loguru import logger

# Global variables to store Redis state
redis_process = None  # Will be set only if we launched Redis
redis_client = None
redis_launched_by_us = False  # Flag to track if we launched Redis

# Get the project root directory
project_root = Path(__file__).parent.parent.parent.parent

# Configure directories
logs_dir = project_root / "logs"
db_dir = project_root / "db"

# Store logger IDs for proper cleanup
logger_ids = []
logger_configured = False


def setup_directories():
    """Set up necessary directories for Redis and logging."""
    global logs_dir, db_dir

    # Create logs directory if it doesn't exist
    if not logs_dir.exists():
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created logs directory at {logs_dir}")
        except PermissionError:
            # Fall back to a directory we can write to
            logs_dir = Path.home() / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(
                f"Using fallback logs directory at {logs_dir} due to permission error"
            )

    # Create db directory if it doesn't exist
    if not db_dir.exists():
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created Redis database directory at {db_dir}")
        except PermissionError:
            # Fall back to a directory we can write to
            db_dir = Path.home() / "db"
            db_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(
                f"Using fallback Redis database directory at {db_dir} "
                f"due to permission error"
            )


def configure_logger():
    """Configure logger to write to both console and file."""
    global logger_ids, logger_configured

    # Only configure once
    if logger_configured:
        return

    # Remove existing handlers
    logger.remove()

    # Clear any existing IDs
    for id in logger_ids:
        try:
            logger.remove(id)
        except ValueError:
            pass

    logger_ids = []

    # Add stderr handler
    stderr_id = logger.add(sys.stderr, level="INFO")
    logger_ids.append(stderr_id)

    # Add file handler
    try:
        file_id = logger.add(
            logs_dir / "mcp_suite.log",
            rotation="10 MB",
            retention="1 week",
            level="DEBUG",
            backtrace=True,
            diagnose=True,
            enqueue=True,  # Use queue to avoid blocking
            catch=True,  # Catch exceptions
        )
        logger_ids.append(file_id)
    except Exception as e:
        logger.warning(f"Could not configure file logger: {e}")

    logger_configured = True


def cleanup_logger():
    """Clean up logger handlers to avoid errors on exit."""
    global logger_ids, logger_configured

    # Remove all handlers
    logger.remove()
    logger_ids = []
    logger_configured = False


def get_db_dir():
    """Get the database directory path.

    Returns:
        Path: The database directory path
    """
    return db_dir
