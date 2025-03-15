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

import datetime
import re
import subprocess
import time
from pathlib import Path

# Create a separate logger for pytest runs
from loguru import logger

# Import the service and utility modules
from mcp_suite.servers.qa.service.pytest import process_pytest_results
from mcp_suite.servers.qa.utils.decorators import exception_handler
from mcp_suite.servers.qa.utils.git_utils import get_git_root

# Get the path to the logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(exist_ok=True)

# Generate a timestamp for the log file
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
PYTEST_LOG_FILE = LOGS_DIR / f"pytest_runs_{timestamp}.log"

# Remove all existing handlers for this logger
logger.remove()

# Configure logger to write to stdout with colors
# logger.add(
#     sys.stdout,
#     colorize=False,
#     format=(
#         "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
#         "<level>{level: <8}</level> | "
#         "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
#         "<level>{message}</level>"
#     ),
#     level="INFO",
# )

# Configure logger to write to a pytest-specific log file
logger.add(
    PYTEST_LOG_FILE,
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    ),
    level="DEBUG",
    mode="w",  # Overwrite the file if it exists (shouldn't happen with timestamp)
)

logger.info(f"Pytest logging initialized. Log file: {PYTEST_LOG_FILE}")


@exception_handler()
async def run_pytest(file_path: str):
    """
    Run pytest tests using subprocess in the git parent directory.

    This function finds the git root directory and runs pytest from there.
    It generates JSON reports for test results and coverage, and analyzes
    the results to provide helpful feedback.

    Args:
        file_path: Path to the file or directory ato test
                  Example: src/mcp_suite/base/redis_db/tests/test_redis_manager.py
                  Use "." to run all tests

    Returns:
        dict: A dictionary containing test results and instructions
    """
    logger.info(f"Running pytest on {file_path}")

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
        logger.debug(f"Using specified file path: {file_path}")
    else:
        logger.debug("Running tests on all files")

    cmd.extend(
        [
            "--json-report",
            "--json-report-file=./reports/pytest_results.json",
            f"--cov={Path(file_path).resolve().parent.parent.as_posix()}",
            "--cov-report=json:./reports/coverage.json",
        ]
    )

    logger.info(f"Executing command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(git_root), text=True, capture_output=True)
    logger.debug(f"Command exit code: {result.returncode}")

    # Check for segmentation fault in stderr
    segfault_match = re.search(r"Fatal Python error: Segmentation fault", result.stderr)
    if segfault_match:
        # Combine stdout and stderr to capture the full context
        full_output = result.stdout + "\n" + result.stderr

        # Get the position of the segmentation fault message in the combined output
        segfault_pos = full_output.find("Fatal Python error: Segmentation fault")

        # Look for test file path pattern before the segmentation fault
        # This pattern matches something like
        # "src/mcp_suite/system_tray/core/tests/test_app.py E"
        test_file_match = re.search(r"(src/.*?\.py\s+[EF])", full_output[:segfault_pos])

        if test_file_match:
            # If we found a test file path, include it in the output
            test_file_pos = test_file_match.start()
            segfault_output = full_output[test_file_pos:]
        else:
            # Otherwise just return from the segmentation fault message
            segfault_output = full_output[segfault_pos:]

        logger.error(f"Segmentation fault detected: {segfault_output}")

        # Extract the file path from the test_file_match if available
        file_info = ""
        if test_file_match:
            file_info = test_file_match.group(1).strip()

        return {
            "Status": "Error",
            "Message": "Fatal Python error: Segmentation fault detected",
            "SegfaultOutput": segfault_output,
            "Instructions": (
                f"A segmentation fault was detected while running tests in {file_info}. "
                "This is typically caused by a memory access violation in C extensions. "
                "Check for any C extensions being used and ensure they're properly "
                "installed. "
                "If this test involves Qt objects (PyQt/PySide), consider using "
                "pytest-qt "
                "which provides proper setup/teardown for Qt tests and can prevent "
                "segmentation faults. "
                "Install with: uv add pytest-qt and use the @pytest.mark.qt decorator "
                "on your tests."
            ),
        }

    # Check if pytest command failed to execute properly
    if result.returncode != 0:
        # Log the full output for debugging
        logger.error(f"Pytest failed with exit code {result.returncode}")
        logger.debug(f"Pytest stdout: {result.stdout}")
        logger.debug(f"Pytest stderr: {result.stderr}")

        # Combine stdout and stderr for a more complete picture
        full_output = result.stdout + "\n" + result.stderr

        # If JSON report doesn't exist, return a generic error
        if not Path(git_root / "reports" / "pytest_results.json").exists():
            logger.error("JSON report file not found")
            return {
                "Status": "Error",
                "Message": f"Pytest failed with exit code {result.returncode}",
                "Output": full_output,
                "Instructions": (
                    "There was an error running pytest. Please check the output above "
                    "for details on what went wrong. This could be due to test "
                    "failures, "
                    "collection errors, or issues with the pytest configuration."
                ),
            }
        else:
            # Even if the JSON report exists, log a warning about the non-zero exit code
            logger.warning(
                "Pytest returned non-zero exit code but JSON report exists. "
                "Proceeding with caution."
            )
            # We'll continue processing the JSON report, but include a note about
            # the exit code

    logger.debug("Waiting for file system to sync...")
    time.sleep(1)

    # Process the results to get both collection errors and test failures
    logger.info("Processing pytest results")
    processed_results = process_pytest_results("./reports/pytest_results.json")

    # Check for collection errors first
    if processed_results.failed_collections:
        # Return the first collection error to fix
        error = processed_results.failed_collections[0]
        logger.warning(f"Collection error found: {error.model_dump()}")

        return {
            "Failed Collection": error.model_dump(),
            "Exit Code": result.returncode,
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
        logger.warning(f"Test failure found: {failure.model_dump()}")

        return {
            "Failed Tests": failure.model_dump(),
            "Exit Code": result.returncode,
            "Instructions": (
                "Explain what's happening and suggest how to fix it."
                "Once you've made the changes, call the run_pytest tool again"
            ),
        }

    # If no failures of any kind but exit code is non-zero, return a warning
    if result.returncode != 0:
        logger.warning(
            "Pytest returned non-zero exit code but no failures were detected in the "
            "JSON report. This could indicate an issue with the test runner or "
            "coverage reporting."
        )
        return {
            "Status": "Warning",
            "Summary": processed_results.summary.model_dump(),
            "Exit Code": result.returncode,
            "Message": (
                "Tests appear to have passed according to the JSON report, but pytest "
                f"returned a non-zero exit code ({result.returncode}). This could "
                "indicate an issue with the test runner, coverage reporting, or other "
                "pytest plugins."
            ),
            "Output": result.stdout + "\n" + result.stderr,
            "Instructions": (
                "Review the output above to understand why pytest returned a "
                "non-zero exit code. This might be due to coverage issues, deprecation "
                "warnings, or other non-test-related problems."
            ),
        }

    # If no failures of any kind, return success
    logger.info("All tests passed successfully!")
    return {
        "Status": "Success",
        "Summary": processed_results.summary.model_dump(),
        "Exit Code": result.returncode,
        "Message": (
            "Excellent work! All tests passed successfully with no errors "
            "or failures detected. Your code is looking great!"
        ),
        "Instructions": (
            "Let's keep the momentum going! Call the mcp tool run_coverage to analyze "
            "code coverage and make sure we've tested everything thoroughly."
        ),
    }
