"""
Configuration package for development servers.
"""

# Import and configure the logger
from pathlib import Path

from .constants import ReportPaths
from .logger import (
    configure_logger,
    logger,
    set_log_file,
    setup_logger_with_standardized_file,
)
from .tools import (
    clear_logs,
    get_current_log_file,
    read_log,
)

# Set up the logger with logs directory
LOGS_DIR = Path(__file__).parents[1] / "logs"
LOGS_DIR.mkdir(exist_ok=True)
setup_logger_with_standardized_file(LOGS_DIR)

logger.info("SaagaLint logging initialized")

__all__ = [
    "logger",
    "ReportPaths",
    "configure_logger",
    "set_log_file",
    "read_log",
    "clear_logs",
    "get_current_log_file",
]
