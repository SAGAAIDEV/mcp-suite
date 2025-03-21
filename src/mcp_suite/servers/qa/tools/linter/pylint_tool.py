"""
Pylint tool for the SaagaLint MCP server.

This module provides a tool for running pylint on Python code and reporting errors.
It integrates with the MCP server to provide a unified interface for code quality checks.

Features:
- Detect pylint errors in Python code
- Report the first error found for fixing
- Validate Python file paths
"""

from mcp_suite.servers.qa.utils.decorators import tool_flow
from mcp_suite.servers.qa.utils.tools import call_tool

from .lib.pylint import get_pylint_error


@tool_flow(continue_message=call_tool("pylint_report"))
async def pylint_report(
    path: str,
):
    """
    Run pylint on the specified path and return the results.

    This tool checks for pylint errors in the specified file or directory and returns
    the first error found. If no errors are found, it returns a success message.

    Args:
        path: The path to the file or directory to check for pylint errors
        fix: Whether to attempt to fix the errors automatically (currently not
             implemented)

    Returns:
        A ToolResult object with status and message about pylint errors
    """

    # First validate that the path is a valid Python file
    return get_pylint_error(path)
