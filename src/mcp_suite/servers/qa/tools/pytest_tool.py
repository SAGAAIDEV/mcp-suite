"""
Pytest tool for the SaagaLint MCP server.

This module provides a tool for running pytest tests and analyzing the results.
It integrates with the MCP server to provide a unified interface for running tests
and reporting results.

Features:
- Run pytest tests on specified files or directories
- Generate JSON reports for test results
- Generate coverage reports
- Analyze test failures and collection errors
- Provide helpful instructions for fixing issues
"""

import subprocess
import time
from pathlib import Path

# Remove logger imports
# from mcp_suite.servers.qa import logger as main_logger
from mcp_suite.servers.qa.service.pytest import process_pytest_results
from mcp_suite.servers.qa.utils.decorators import exception_handler
from mcp_suite.servers.qa.utils.git_utils import get_git_root

# from mcp_suite.servers.qa.utils.logging_utils import get_component_logger

# Remove logger initialization
# logger = get_component_logger("pytest")


@exception_handler()
async def run_pytest(file_path: str):
    """
    Run pytest tests using subprocess in the git parent directory.

    This function finds the git root directory and runs pytest from there.
    It generates JSON reports for test results and coverage, and analyzes
    the results to provide helpful feedback.

    Args:
        file_path: Path to the file or directory to test
                  Example: src/mcp_suite/base/redis_db/tests/test_redis_manager.py
                  Use "." to run all tests

    Returns:
        dict: A dictionary containing test results and instructions
    """
    # Find git root directory
    git_root = get_git_root()

    # Change to git root directory and run pytest
    cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "pytest",
    ]
    if file_path != ".":
        cmd.append(file_path)
    cmd.extend(
        [
            "--json-report",
            "--json-report-file=./reports/pytest_results.json",
            f"--cov={Path(file_path).resolve().parent.parent.as_posix()}",
            "--cov-report=json:./reports/coverage.json",
        ]
    )

    result = subprocess.run(cmd, cwd=str(git_root), text=True, capture_output=True)

    # Check if pytest command failed to execute properly
    if (
        result.returncode != 0
        and not Path(git_root / "reports" / "pytest_results.json").exists()
    ):
        return {
            "Status": "Error",
            "Message": f"Pytest failed with error: {result.stderr}",
            "Instructions": (
                "There was an error running pytest. Please check if pytest "
                "is installed correctly and that the file path is valid."
            ),
        }

    time.sleep(1)

    # Process the results to get both collection errors and test failures
    processed_results = process_pytest_results("./reports/pytest_results.json")

    # Check for collection errors first
    if processed_results.failed_collections:
        # Return the first collection error to fix
        error = processed_results.failed_collections[0]

        return {
            "Failed Collection": error.model_dump(),
            "Instructions": (
                "Don't worry, we've got this! Let's fix this collection error first "
                "before running tests. This is typically an import error or "
                "missing module. I'll help you understand the error and "
                "find a solution. We'll get your tests running in no time!"
            ),
        }

    # If no collection errors, check for test failures
    if processed_results.failed_tests:
        failure = processed_results.failed_tests[0]

        return {
            "Failed Tests": failure.model_dump(),
            "Instructions": (
                "You're making great progress! Let's tackle this test failure together. "
                "I'll explain what's happening and suggest how to fix it. "
                "Once you've made the changes, call the run_pytest tool again and "
                "we'll see if we've resolved it. Remember, test failures are just "
                "stepping stones to better code!"
            ),
        }

    # If no failures of any kind, return success
    return {
        "Status": "Success",
        "Summary": processed_results.summary.model_dump(),
        "Message": (
            "Excellent work! All tests passed successfully with no errors "
            "or failures detected. Your code is looking great!"
        ),
        "Instructions": (
            "Let's keep the momentum going! Call the mcp tool run_coverage to analyze "
            "code coverage and make sure we've tested everything thoroughly."
        ),
    }
