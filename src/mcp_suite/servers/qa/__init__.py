"""
SaagaLint - A comprehensive linting and testing tool for Python projects.

SaagaLint provides a set of tools for running tests, checking code coverage,
and performing static analysis on Python code. It integrates with pytest,
coverage, and various linting tools to provide a unified interface for
code quality checks.

Components:
- pytest: Run tests and analyze results
- coverage: Check code coverage and identify untested code
- autoflake: Detect and fix unused imports and variables

Logging is configured to write to a file in the logs directory.
A new log file is created each time the server runs with a timestamp in the filename.
"""

import datetime
from pathlib import Path

from loguru import logger

# Get the path to the logs directory
LOGS_DIR = Path(__file__).parent / "logs"

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(exist_ok=True)

# Generate a timestamp for the log file
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOGS_DIR / f"saagalint_{timestamp}.log"

# Remove all existing handlers
logger.remove()

# Configure logger to write to stdout with colors
# logger.add(
#     sys.stdout,
#     colorize=False,
#     format=(
#         "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
#         "<level>{level: <8}</level> | "
#         "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
#         "<level>{message}</level>"
#     ),
#     level="INFO",
# )

# Configure logger to write to a new file each time with timestamp in filename
logger.add(
    LOG_FILE,
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    ),
    level="DEBUG",
    mode="w",  # Overwrite the file if it exists (shouldn't happen with timestamp)
)

logger.info(f"Logging initialized. Log file: {LOG_FILE}")

# Export the logger for use in other modules
__all__ = ["logger", "LOG_FILE"]
