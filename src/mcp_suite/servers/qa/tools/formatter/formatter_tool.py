"""
Formatter tool for the SaagaLint MCP server.

This module provides a tool for automatically formatting Python code.
It integrates with the MCP server to provide a unified interface for code
formatting.

Features:
- Runs autoflake to remove unused imports and variables
- Runs isort to fix import ordering
- Runs black to fix formatting and long lines
"""

from mcp_suite.servers.qa.config import logger
from mcp_suite.servers.qa.models.tool_result import NextAction, ToolResult, ToolStatus
from mcp_suite.servers.qa.tools.linter.flake8_report import flake8_report
from mcp_suite.servers.qa.utils.git_utils import get_git_root

from .lib.autoflake import run_autoflake
from .lib.black import run_black
from .lib.isort import run_isort


async def formatter(file_path: str = "src/", max_line_length: int = 89):
    """
    Run code formatters on specified files or directories.

    This function runs a series of code formatters to automatically fix
    common code style issues:
    - autoflake: removes unused imports and variables
    - isort: fixes import ordering
    - black: fixes formatting and long lines

    Args:
        file_path: Path to the file or directory to format (relative to git root)
                  Defaults to "src/" if not specified
        max_line_length: Maximum line length (default: 89)

    Returns:
        ToolResult: A ToolResult object containing formatting status and details
    """
    logger.info(
        f"Running formatters on {file_path} with " f"max_line_length={max_line_length}"
    )

    # Find git root directory
    git_root = get_git_root()
    logger.debug(f"Git root directory: {git_root}")

    # Run autoflake to fix unused imports and variables
    autoflake_result = run_autoflake(file_path, git_root)

    # Run isort to fix import ordering
    isort_result = run_isort(file_path, git_root, max_line_length)

    # Run black to fix formatting and long lines
    black_result = run_black(file_path, git_root, max_line_length)

    # Check if all formatters completed successfully
    all_success = all(
        result.returncode == 0
        for result in [autoflake_result, isort_result, black_result]
    )

    status = ToolStatus.SUCCESS if all_success else ToolStatus.FAILURE

    details = {
        "autoflake": "Completed" if autoflake_result.returncode == 0 else "Failed",
        "isort": "Completed" if isort_result.returncode == 0 else "Failed",
        "black": "Completed" if black_result.returncode == 0 else "Failed",
    }

    message = (
        "Code formatting completed successfully"
        if all_success
        else "Some formatters failed"
    )
    message += f"\nDetails: {details}"

    return ToolResult(
        status=status,
        message=message,
        next_action=NextAction(tool=flake8_report),
    )
