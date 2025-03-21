"""
Autoflake tool for the SaagaLint MCP server.

This module provides a tool for detecting and fixing unused imports and variables
in Python code. It integrates with the MCP server to provide a unified interface
for code quality checks.

Features:
- Detect unused imports and variables
- Automatically fix issues (optional)
- Generate detailed reports of issues
- Provide helpful instructions for fixing issues manually
- Integration with flake8 for additional linting
- Generate flake8 reports for further analysis
"""

import json

from mcp_qa.config import logger
from mcp_qa.models.tool_result import ToolResult, ToolStatus
from mcp_qa.tools.linter.lib.flake8 import (
    process_flake8_issues,
    run_flake8_command,
    set_output_file,
)
from mcp_qa.tools.linter.pylint_tool import pylint_report
from mcp_qa.utils.decorators import exception_handler, tool_flow
from mcp_qa.utils.git_utils import get_git_root
from mcp_qa.utils.tools import call_tool


@exception_handler()
@tool_flow(
    continue_message=(
        "Call the mcp tool flake8_report again until there are no more errors."
    ),
    exception_message=f"Diagnose {__file__} and its imports to see what went wrong.",
)
async def flake8_report(
    file_path: str,
    max_line_length: int = 89,
    ignore: str = "E203,W503",
):
    """
    Run flake8 analysis on specified files or directories.

    This function analyzes Python code for style and quality issues
    and generates a flake8 report.

    Args:
        file_path: Path to the file or directory to analyze (relative to git root)
        max_line_length: Maximum line length for flake8 (default: 89)
        ignore: Comma-separated list of error codes to ignore (default: "E203,W503")

    Returns:
        ToolResult: A ToolResult object containing analysis results and instructions
    """
    try:
        logger.info(f"Running flake8 analysis on {file_path}")

        # Find git root directory
        git_root = get_git_root()
        logger.debug(f"Git root directory: {git_root}")

        # Validate that the path is a Python file
        # full_path = git_root / file_path
        # if not is_valid_python_path(str(full_path)):
        #     error_message = f"Invalid Python file path: {file_path}"
        #     logger.error(error_message)
        #     return ToolResult(status=ToolStatus.ERROR, message=error_message)

        # Set the output file path
        report_file_path = set_output_file(git_root)

        # Run the flake8 command
        success, error_message = run_flake8_command(
            file_path, report_file_path, git_root, max_line_length, ignore
        )

        if not success:
            return ToolResult(
                status=ToolStatus.ERROR,
                message=error_message,
            )

        all_warnings = process_flake8_issues(report_file_path)

        # Get the next flake8 issue to fix

        first_error_message = next(iter(all_warnings))
        return ToolResult(
            status=ToolStatus.CONTINUE,
            message=f"Flake8 error found:\n{first_error_message}",
            continue_message=call_tool(flake8_report),
        )
    except StopIteration:
        # If next() doesn't return anything, there are no errors
        return ToolResult(
            status=ToolStatus.SUCCESS,
            message="Flake8 'inting complete! No flake errors found.",
            success_message=call_tool(pylint_report),
        )
    except json.JSONDecodeError as e:
        error_msg = f"Error: Invalid JSON in {report_file_path}: {str(e)}"
        logger.error(error_msg)
        raise

    except Exception as e:
        error_msg = f"Error processing flake8 results: {str(e)}"
        logger.exception(error_msg)
        raise
