"""
Logging tools for the QA package.

This module provides functions for reading and managing log files.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

# Import from logger to avoid circular imports
from mcp_suite.servers.qa.config.logger import CURRENT_LOG_FILE


def get_current_log_file() -> Optional[Path]:
    """Get the current log file path.

    Returns:
        Optional[Path]: The current log file path or None if no log file has been set.
    """
    return CURRENT_LOG_FILE


def read_log(index: int = 0) -> Optional[Dict[str, Any]]:
    """Read and parse the content of a log file based on index.

    Args:
        index: Index of the log file to read. Defaults to 0 (current log).
               Negative indices can be used to access previous logs
               (-1 for the last log, etc.)

    Returns:
        Optional[Dict[str, Any]]: Dictionary containing parsed log entries or None
        if file not found.
    """
    if CURRENT_LOG_FILE is None:
        logger.error("No log file has been set.")
        return None

    log_dir = CURRENT_LOG_FILE.parent

    # Get all log files in the directory sorted by modification time (newest first)
    log_files = sorted(
        [f for f in log_dir.glob("*.log") if f.is_file()],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not log_files:
        logger.error(f"No log files found in {log_dir}")
        return None

    # Handle index
    if index >= len(log_files) or -index > len(log_files):
        logger.error(
            f"Log file index {index} out of range. "
            f"Available range: {-len(log_files)} to {len(log_files) - 1}"
        )
        return None

    target_log = log_files[index]

    try:
        # Read the log file content
        with open(target_log, "r") as f:
            content = f.readlines()

        # Parse JSON entries
        log_entries = []
        for line in content:
            try:
                log_entries.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse log entry: {line}")

        return {
            "file_path": target_log,
            "entries": log_entries,
            "entry_count": len(log_entries),
        }
    except Exception as e:
        logger.error(f"Error reading log file {target_log}: {str(e)}")
        return None


def clear_logs() -> int:
    """Delete all log files in the current log directory except the current one.

    Returns:
        int: Number of files deleted.
    """
    if CURRENT_LOG_FILE is None:
        logger.warning("No current log file set. Cannot clear logs.")
        return 0

    log_dir = CURRENT_LOG_FILE.parent

    # Get all log files excluding the current one
    log_files = [
        f for f in log_dir.glob("*.log") if f.is_file() and f != CURRENT_LOG_FILE
    ]

    deleted_count = 0
    for file_path in log_files:
        try:
            file_path.unlink()
            deleted_count += 1
        except Exception as e:
            logger.error(f"Error deleting log file {file_path}: {str(e)}")

    logger.info(f"Cleared {deleted_count} log files from {log_dir}")
    return deleted_count
