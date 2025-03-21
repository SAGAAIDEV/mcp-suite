"""
Utility functions for the QA package configuration.

This module provides utility functions used by the logger and other
configuration components of the QA package.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Try to import wonderwords for random noun generation
try:
    from wonderwords import RandomWord

    WONDERWORDS_AVAILABLE = True
except ImportError:
    WONDERWORDS_AVAILABLE = False


def get_random_noun(word_min_length: int = 4, word_max_length: int = 12) -> str:
    """Generate a random noun using the wonderwords library.

    Args:
        word_min_length: Minimum length of the word
        word_max_length: Maximum length of the word

    Returns:
        str: A random noun.
    """
    try:
        if WONDERWORDS_AVAILABLE:
            r = RandomWord()
            # Get a random noun with length constraints
            return r.word(
                include_parts_of_speech=["nouns"],
                word_min_length=word_min_length,
                word_max_length=word_max_length,
            )
        else:
            raise ImportError("wonderwords not available")
    except Exception:
        # Simple fallback if wonderwords fails
        return f"log_{random.randint(1000, 9999)}"


def json_serializer(record: Dict[str, Any]) -> str:
    """
    Serialize log record to JSON format.

    Args:
        record: The log record to serialize

    Returns:
        str: JSON formatted log string
    """
    # Extract the most important fields for JSON serialization
    log_data = {
        "timestamp": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f"),
        "level": record["level"].name,
        "message": record["message"],
        "name": record["name"],
        "function": record["function"],
        "line": record["line"],
    }

    # Add exception info if present
    if record["exception"]:
        log_data["exception"] = record["exception"].rstrip()

    # Convert to JSON string
    return json.dumps(log_data)


def get_standardized_log_filename(
    log_dir: Optional[Union[str, Path]] = None,
    word_min_length: int = 4,
    word_max_length: int = 12,
) -> Path:
    """Generate a standardized log file name with date, time and random noun.

    Format: qa_noun_yyyymmdd_hhmmss.log (e.g., qa_dragon_20230814_153045.log)

    This format ensures:
    - Human-readable filenames with random nouns for easier reference
    - Chronological sorting when listed alphabetically
    - Uniqueness through combination of noun and timestamp

    Args:
        log_dir: Optional directory path where the log file will be stored.
               If None, only the filename is returned without a directory.
        word_min_length: Minimum length of the noun
        word_max_length: Maximum length of the noun

    Returns:
        Path: The standardized log file path.
    """
    # Get current date and time
    now = datetime.now()

    # Format with strftime for better maintainability
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    # Include a random noun for better readability
    noun = get_random_noun(word_min_length, word_max_length)
    filename = f"qa_{noun}_{timestamp}.log"

    # Return full path if directory is provided
    if log_dir is not None:
        if isinstance(log_dir, str):
            log_dir = Path(log_dir)
        return log_dir / filename

    return Path(filename)
