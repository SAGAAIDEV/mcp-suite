"""Module for processing and organizing Pylint error reports.

This module provides functionality to parse, group, and structure Pylint
error outputs into a hierarchical data model for easier consumption
in the QA service.
"""

import json
import subprocess
from collections import defaultdict

from mcp_qa.models.tool_result import ToolResult, ToolStatus
from mcp_qa.utils.git_utils import get_git_root

from ..models.pylint_models import PylintError


def get_pylint_json(path):
    """Execute pylint on specified path and return the results as structured data.

    Runs pylint with JSON output format to get machine-readable linting results
    from the specified path.

    Args:
        path: The file or directory path to run pylint on

    Returns:
        List of dictionaries containing pylint results, empty list if no errors found
    """
    result = subprocess.run(
        ["uv", "run", "pylint", "--output-format=json", path],
        capture_output=True,
        cwd=get_git_root(),
        text=True,
        check=False,
    )
    pylint_results = json.loads(result.stdout) if result.stdout else []
    return pylint_results


def get_pylint_files(path: str):
    """
    Gets a list of files with pylint errors
    path:
    """
    pylint_results = get_pylint_json(path)
    error_files = {error["path"] for error in pylint_results}
    return error_files


def group_pylint_results(pylint_results: list[dict]) -> list[str]:
    errors = [PylintError(**error) for error in pylint_results]

    # Double-check after parsing - in case all were filtered out somehow
    if not errors:
        return None

    grouped_errors = defaultdict(list)
    for error in errors:
        grouped_errors[f"{error.message_id}-{error.symbol}"].append(error.format())

    # Format the output
    errors = [f"{key}\n{chr(10).join(val)}" for key, val in grouped_errors.items()]

    # Return None if no errors after grouping (unlikely but for safety)
    return errors if errors else None


def get_pylint_error(path: str) -> ToolResult:
    """
    Get the first pylint error from the specified path.

    Args:
        path: The path to the file or directory to check for pylint errors

    Returns:
        A ToolResult object with status and message about pylint errors
    """
    pylint_results = get_pylint_json(path)

    if not pylint_results:
        return ToolResult(
            status=ToolStatus.SUCCESS,
            message="No pylint errors found. Great job!",
        )

    grouped_errors = group_pylint_results(pylint_results)

    if not grouped_errors:
        return ToolResult(
            status=ToolStatus.SUCCESS,
            message="No pylint errors found. Great job!",
        )

    # Return the first error
    first_error = grouped_errors[0]

    return ToolResult(
        status=ToolStatus.CONTINUE,
        message=f"Pylint error found:\n{first_error}",
    )
