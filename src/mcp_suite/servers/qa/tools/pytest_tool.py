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

from mcp_suite.servers.qa import logger as main_logger
from mcp_suite.servers.qa.service.pytest import process_pytest_results
from mcp_suite.servers.qa.utils.decorators import exception_handler
from mcp_suite.servers.qa.utils.git_utils import get_git_root
from mcp_suite.servers.qa.utils.logging_utils import get_component_logger

# Get a component-specific logger
logger = get_component_logger("pytest")


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
    logger.info(f"Running pytest on: {file_path}")
    main_logger.info(f"Running pytest on: {file_path}")

    # Find git root directory
    git_root = get_git_root()
    logger.debug(f"Git root directory: {git_root}")

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

    logger.debug(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(git_root), text=True, capture_output=True)
    logger.debug(f"Command exit code: {result.returncode}")

    if result.stdout:
        logger.debug(f"Command stdout: {result.stdout}")

    if result.stderr:
        logger.warning(f"Command stderr: {result.stderr}")

    time.sleep(1)

    # Process the results to get both collection errors and test failures
    logger.info("Processing pytest results")
    processed_results = process_pytest_results("./reports/pytest_results.json")
    logger.debug(f"Processed results: {processed_results}")

    # Check for collection errors first
    if processed_results.failed_collections:
        # Return the first collection error to fix
        error = processed_results.failed_collections[0]
        logger.warning(f"Collection error detected: {error}")
        main_logger.warning(f"Collection error detected in pytest: {error}")

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
        logger.warning(f"Test failure detected: {failure}")
        main_logger.warning(f"Test failure detected in pytest: {failure}")

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
    logger.info("All tests passed successfully")
    main_logger.info("All pytest tests passed successfully")

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
