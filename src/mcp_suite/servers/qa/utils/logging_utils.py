"""
Logging utilities for SaagaLint.

This module provides utilities for setting up and configuring loggers
for different components of the SaagaLint system.
"""

from pathlib import Path

from loguru import logger


def setup_component_logger(
    component_name: str, log_level: str = "DEBUG", rotation: str = "10 MB"
) -> logger:
    """
    Set up a logger for a specific component.

    This function creates a logger instance for a specific component,
    with output to both the console and a component-specific log file.
    The log file is overwritten on each run.

    Args:
        component_name: The name of the component (e.g., 'pytest', 'coverage')
        log_level: The minimum log level to record (default: 'DEBUG')
        rotation: When to rotate log files (default: '10 MB')

    Returns:
        A configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(__file__).parent.parent / "logs"
    log_path.mkdir(exist_ok=True)

    # Define log file path for this component
    log_file = log_path / f"{component_name}.log"

    # Create a new logger instance
    component_logger = logger.bind(component=component_name)

    # Add file handler with rotation and mode="w" to overwrite the file on each run
    component_logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
        "{extra[component]} | {name}:{function}:{line} - {message}",
        rotation=rotation,
        diagnose=True,
        mode="w",  # Overwrite the file on each run
    )

    component_logger.info(
        f"{component_name.capitalize()} logger initialized. "
        f"Logs will be written to {log_file}"
    )

    return component_logger


def get_component_logger(component_name: str) -> logger:
    """
    Get a logger for a specific component.

    If the logger doesn't exist, it will be created.

    Args:
        component_name: The name of the component

    Returns:
        A configured logger instance
    """
    return setup_component_logger(component_name)
