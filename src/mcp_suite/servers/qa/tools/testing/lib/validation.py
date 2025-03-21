"""
Validation utilities for pytest and coverage tools.

This module provides functions for validating file paths and module imports
used by the pytest and coverage tools.
"""

from pathlib import Path
from typing import Optional

# from loguru import logger
from mcp_suite.servers.qa.config import logger
from mcp_suite.servers.qa.models.tool_result import (
    NextAction,
    ToolResult,
    ToolStatus,
)
from mcp_suite.servers.qa.utils.files import is_valid_python_path

# Create a logger specifically for validation
validation_logger = logger.bind(component="pytest_validation")


def validate_file_path(file_path: str, tool_function) -> Optional[ToolResult]:
    """
    Validate that the provided file path is a valid Python file.

    Args:
        file_path: Path to the file or directory to test
        tool_function: The function to reference in the NextAction

    Returns:
        ToolResult: Error result if validation fails, None otherwise
    """
    validation_logger.debug(f"Validating file path: {file_path}")

    # Special case for '.' which is used to run all tests
    if file_path == ".":
        return None

    # Check if the file path exists
    path_exists = Path(file_path).exists()
    if not path_exists:
        validation_logger.error(f"Python file path does not exist: {file_path}")
        next_action = NextAction(
            tool=tool_function,
            instructions="Please provide a valid Python file path.",
        )
        return ToolResult(
            status=ToolStatus.ERROR,
            message=f"Invalid Python file path: {file_path}",
            next_action=next_action,
        )

    # Check Python path format - only if the file exists
    python_path_valid = is_valid_python_path(file_path)
    if not python_path_valid:
        validation_logger.error(f"Invalid Python file path format: {file_path}")
        return ToolResult(
            status=ToolStatus.ERROR,
            message=f"Invalid Python file path: {file_path}",
        )

    validation_logger.debug(f"File path validation successful: {file_path}")
    return None  # No error
