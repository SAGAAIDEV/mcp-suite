"""File Utility Functions

This module provides utility functions for file operations related to the
transcriber service.
"""

import os
from pathlib import Path

from loguru import logger

from ..config.config import SUPPORTED_FORMATS


def validate_audio_file(file_path: str) -> tuple[bool, str]:
    """Validate that a file exists and has a supported audio format.

    Args:
        file_path: Path to the audio file to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if the file is valid, False otherwise
        - error_message: Empty string if valid, error message if invalid
    """
    # Check if file exists
    if not os.path.exists(file_path):
        error_msg = f"Audio file not found: {file_path}"
        logger.error(error_msg)
        return False, error_msg

    # Check if file is a file (not a directory)
    if not os.path.isfile(file_path):
        error_msg = f"Path is not a file: {file_path}"
        logger.error(error_msg)
        return False, error_msg

    # Check file format
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in SUPPORTED_FORMATS:
        error_msg = (
            f"Unsupported audio format: {file_ext}. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )
        logger.error(error_msg)
        return False, error_msg

    # Check if file is readable
    try:
        with open(file_path, "rb") as f:
            # Just try to read a byte to check if file is readable
            f.read(1)
    except Exception as e:
        error_msg = f"File is not readable: {file_path}. Error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

    return True, ""


def get_file_size(file_path: str) -> int:
    """Get the size of a file in bytes.

    Args:
        file_path: Path to the file

    Returns:
        Size of the file in bytes, or 0 if the file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {str(e)}")
        return 0


def get_file_info(file_path: str) -> dict:
    """Get information about a file.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with file information
    """
    try:
        path = Path(file_path)
        stats = path.stat()

        return {
            "name": path.name,
            "path": str(path.absolute()),
            "size": stats.st_size,
            "size_human": f"{stats.st_size / 1024 / 1024:.2f} MB",
            "extension": path.suffix.lower(),
            "created": stats.st_ctime,
            "modified": stats.st_mtime,
            "exists": path.exists(),
            "is_file": path.is_file(),
        }
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {str(e)}")
        return {
            "name": os.path.basename(file_path),
            "path": file_path,
            "error": str(e),
            "exists": False,
        }
