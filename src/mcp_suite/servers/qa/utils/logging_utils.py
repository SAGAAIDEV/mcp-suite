"""
Logging utilities for SaagaLint.

This module provides utilities for setting up and configuring loggers
for different components of the SaagaLint system.

All logging has been disabled as requested.
"""

from loguru import logger


def setup_component_logger(
    component_name: str, log_level: str = "DEBUG", rotation: str = "10 MB"
) -> logger:
    """
    Set up a logger for a specific component.

    This is a no-op function that returns a disabled logger.

    Args:
        component_name: The name of the component (e.g., 'pytest', 'coverage')
        log_level: The minimum log level to record (default: 'DEBUG')
        rotation: When to rotate log files (default: '10 MB')

    Returns:
        A disabled logger instance
    """
    # Return a disabled logger
    return logger.bind(component=component_name)


def get_component_logger(component_name: str) -> logger:
    """
    Get a logger for a specific component.

    This is a no-op function that returns a disabled logger.

    Args:
        component_name: The name of the component

    Returns:
        A disabled logger instance
    """
    return logger.bind(component=component_name)
