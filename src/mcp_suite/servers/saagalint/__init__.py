"""
Dev server package initialization.

This module initializes the dev server package and sets up centralized logging
for all modules within the package.
"""

import sys
from pathlib import Path

from loguru import logger

# Create logs directory if it doesn't exist
log_path = Path(__file__).parent / "logs"
log_path.mkdir(exist_ok=True)

# Define log file path - using a single log file for all dev modules
log_file = log_path / "dev_server.log"

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

# Add file handler with overwrite mode
logger.add(
    log_file,
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
    "{name}:{function}:{line} - {message}",
    # backtrace=True,
    diagnose=True,
    mode="w",  # 'w' mode overwrites the file each time
)

logger.info(f"Dev server package initialized. Logs will be written to {log_file}")

# Export the logger and log_file for use in other modules
__all__ = ["logger", "log_file"]
