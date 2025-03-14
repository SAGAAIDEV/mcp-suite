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

Each component has its own logger that writes to a separate log file,
making it easier to track issues and debug problems.
"""

import sys
from pathlib import Path

from loguru import logger

# Create logs directory if it doesn't exist
log_path = Path(__file__).parent / "logs"
log_path.mkdir(exist_ok=True)

# Define log file path for the main logger
main_log_file = log_path / "saagalint.log"

# Remove default handler
logger.remove()

# Add stderr handler for console output
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>",
)

# Add file handler with rotation
logger.add(
    main_log_file,
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
    "{name}:{function}:{line} - {message}",
    rotation="10 MB",
    diagnose=True,
)

logger.info(f"SaagaLint initialized. Main logs will be written to {main_log_file}")
logger.info(
    "Component-specific logs will be written to separate files in the logs directory"
)

# Export the logger for use in other modules
__all__ = ["logger"]
