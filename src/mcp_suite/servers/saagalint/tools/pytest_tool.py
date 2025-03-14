"""Pytest tool for the SaagaLint MCP server."""

import subprocess
import time
from pathlib import Path

from mcp_suite.servers.saagalint import logger
from mcp_suite.servers.saagalint.service.pytest_service import process_pytest_results
from mcp_suite.servers.saagalint.utils.decorators import exception_handler
from mcp_suite.servers.saagalint.utils.git_utils import get_git_root


@exception_handler()
async def run_pytest(file_path: str):
    """Run pytest tests using subprocess in the git parent directory.

    This function finds the git root directory and runs pytest from there.
        file_path: str
        example src/mcp_suite/base/redis_db/tests/test_redis_manager.py
        or if you are told to run on all the files use . for root to get all tests
    """
    logger.info(f"Running pytest on: {file_path}")

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

    logger.debug(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(git_root), text=True, capture_output=True)
    logger.debug(f"Command exit code: {result.returncode}")

    if result.stdout:
        logger.debug(f"Command stdout: {result.stdout}")

    if result.stderr:
        logger.warning(f"Command stderr: {result.stderr}")

    time.sleep(1)

    # Process the results to get both collection errors and test failures
    processed_results = process_pytest_results("./reports/pytest_results.json")

    # Check for collection errors first
    if processed_results.failed_collections:
        # Return the first collection error to fix
        logger.warning(
            f"Collection error detected: {processed_results.failed_collections[0]}"
        )
        return {
            "Failed Collection": processed_results.failed_collections[0].model_dump(),
            "Instructions": (
                "Don't worry, we've got this! Let's fix this collection error first "
                "before running tests. This is typically an import error or "
                "missing module. I'll help you understand the error and "
                "find a solution. We'll get your tests running in no time!"
            ),
        }

    # If no collection errors, check for test failures
    if processed_results.failed_tests:
        logger.warning(f"Test failure detected: {processed_results.failed_tests[0]}")
        return {
            "Failed Tests": processed_results.failed_tests[0].model_dump(),
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
