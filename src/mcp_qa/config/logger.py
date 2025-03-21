"""
Logger configuration for the QA package.

This module provides functions for configuring and managing the logger used
throughout the QA package.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple, Union

from loguru import logger

from mcp_qa.config.utils import (
    get_standardized_log_filename,
    json_serializer,
)

# Global sink IDs
STDOUT_SINK_ID = None
FILE_SINK_ID = None
CURRENT_LOG_FILE = None


def configure_logger(
    log_file: Path,
    stdout_sink_id: Optional[int] = None,
    file_sink_id: Optional[int] = None,
) -> Tuple[int, int]:
    """Configure logger with stdout and file sinks.

    Args:
        log_file: Path to the log file.
        stdout_sink_id: ID of existing stdout sink to remove.
        file_sink_id: ID of existing file sink to remove.

    Returns:
        Tuple[int, int]: IDs of the new stdout and file sinks.
    """
    global STDOUT_SINK_ID, FILE_SINK_ID, CURRENT_LOG_FILE

    # Remove existing sinks if any
    if stdout_sink_id is not None:
        logger.remove(stdout_sink_id)
    if file_sink_id is not None:
        logger.remove(file_sink_id)

    # Configure logger to write to stdout with colors (human-readable format)
    new_stdout_sink_id = logger.add(
        sys.stdout,
        colorize=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level="INFO",
    )

    # Configure logger to write to file in JSON format for machine readability
    new_file_sink_id = logger.add(
        log_file,
        rotation=None,  # No rotation
        retention=1,  # Keep only the latest file
        serialize=json_serializer,  # Use JSON serializer
        level="DEBUG",
        mode="w",  # Overwrite the file each time
    )

    STDOUT_SINK_ID = new_stdout_sink_id
    FILE_SINK_ID = new_file_sink_id
    CURRENT_LOG_FILE = log_file

    logger.info(f"Logging reconfigured. Log file: {log_file}")

    return new_stdout_sink_id, new_file_sink_id


def set_log_file(
    new_log_path: Union[str, Path],
    stdout_sink_id: Optional[int] = None,
    file_sink_id: Optional[int] = None,
) -> Tuple[Path, int, int]:
    """Set a new log file path and reconfigure the logger.

    Args:
        new_log_path: New path for the log file. Can be a string or Path object.
        stdout_sink_id: ID of existing stdout sink to remove.
        file_sink_id: ID of existing file sink to remove.

    Returns:
        Tuple[Path, int, int]: The new log file path and sink IDs.
    """
    global STDOUT_SINK_ID, FILE_SINK_ID

    # Convert to Path if string
    if isinstance(new_log_path, str):
        new_log_path = Path(new_log_path)

    # Create parent directory if it doesn't exist
    new_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Use global sink IDs if not provided
    if stdout_sink_id is None:
        stdout_sink_id = STDOUT_SINK_ID
    if file_sink_id is None:
        file_sink_id = FILE_SINK_ID

    # Reconfigure the logger
    new_stdout_sink_id, new_file_sink_id = configure_logger(
        new_log_path, stdout_sink_id, file_sink_id
    )

    return new_log_path, new_stdout_sink_id, new_file_sink_id


def change_file_sink(
    new_log_path: Union[str, Path],
) -> int:
    """Change only the file sink while preserving the stdout sink.

    Args:
        new_log_path: New path for the log file. Can be a string or Path object.

    Returns:
        int: The new file sink ID.
    """
    global FILE_SINK_ID, CURRENT_LOG_FILE

    # Convert to Path if string
    if isinstance(new_log_path, str):
        new_log_path = Path(new_log_path)

    # Create parent directory if it doesn't exist
    new_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing file sink if any
    if FILE_SINK_ID is not None:
        logger.remove(FILE_SINK_ID)

    # Configure logger to write to new file in JSON format
    new_file_sink_id = logger.add(
        new_log_path,
        rotation=None,  # No rotation
        retention=1,  # Keep only the latest file
        serialize=json_serializer,  # Use JSON serializer
        level="DEBUG",
        mode="w",  # Overwrite the file each time
    )

    FILE_SINK_ID = new_file_sink_id
    CURRENT_LOG_FILE = new_log_path

    logger.info(f"File sink changed. New log file: {new_log_path}")

    return new_file_sink_id


def setup_logger_with_standardized_file(
    log_dir: Union[str, Path],
    word_min_length: int = 4,
    word_max_length: int = 12,
) -> Path:
    """Set up a logger with a standardized log file name in the specified directory.

    Args:
        log_dir: Directory path where the log file will be stored.
        word_min_length: Minimum length of the noun
        word_max_length: Maximum length of the noun

    Returns:
        Path: The path to the created log file.
    """
    # Generate standardized log filename with the given directory
    log_file_path = get_standardized_log_filename(
        log_dir, word_min_length, word_max_length
    )

    # Create parent directory if it doesn't exist
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Set up the logger with the standardized log file
    global STDOUT_SINK_ID, FILE_SINK_ID
    STDOUT_SINK_ID, FILE_SINK_ID = configure_logger(log_file_path)

    return log_file_path
