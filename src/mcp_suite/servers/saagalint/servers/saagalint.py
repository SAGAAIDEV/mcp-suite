import json
import subprocess
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from mcp_suite.servers.saagalint.utils.decorators import exception_handler

# Import logging configuration
from src.mcp_suite.servers.saagalint import logger

from ..service.autoflake_service import process_autoflake_results

# Import services
from ..service.coverage_service import process_coverage_json
from ..service.pytest_service import process_pytest_results

# Import utils
from ..utils.git_utils import get_git_root

# Configure logging


mcp = FastMCP("precommit", settings={"host": "localhost", "port": "8081"})


@mcp.tool()
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


@mcp.tool()
@exception_handler()
async def run_coverage(file_path):
    """
    file_path: THe file path you would like from the coverage report, make it relative
    """
    logger.info("Running coverage analysis")

    coverage_results_file = get_git_root() / "reports/coverage.json"
    result = process_coverage_json(coverage_results_file)
    # Log each coverage issue for debugging
    for issue in result:
        issue_data = issue.model_dump()
        logger.debug(f"Coverage issue details: {json.dumps(issue_data, indent=2)}")
    if file_path:
        result = next((item for item in result if item.file_path == file_path), None)
    else:
        result = str(result.values()[0])

    if result:
        logger.warning(f"Coverage issues found: {len(result)} issues")
        return {
            "Message": str(result),
            "Instructions": (
                "We're making great progress! Let's improve the test coverage "
                "for these areas. I'll help you understand what needs to be tested "
                "and how to write effective tests for the missing coverage. "
                "Once you've added the tests, run the pytest tool again. "
                "Remember, better test coverage means more reliable code!"
            ),
        }
    else:
        logger.info("Coverage is complete!")
        return {
            "Message": (
                "Outstanding job! Your test coverage is complete and comprehensive. "
                "You're doing excellent work!"
            ),
            "Instructions": (
                "You're on a roll! Let's continue with running the linting tools "
                "to make sure your code style is as perfect as your test coverage. "
                "Keep up the great work!"
            ),
        }


@mcp.tool()
@exception_handler()
async def run_autoflake(file_path: str = ".", fix: bool = True):
    """Run autoflake analysis on specified files or directories.

    Args:
        file_path: Path to the file or directory to analyze (relative to git root)
                  Defaults to current directory if not specified
        fix: Boolean flag to automatically apply fixes (default: False)

    Returns:
        Status report with issue details and instructions for fixing
    """
    logger.info(f"Running autoflake on: {file_path} with fix={fix}")

    # Find git root directory
    git_root = get_git_root()
    reports_dir = git_root / "reports"
    reports_dir.mkdir(exist_ok=True)

    # If fix is True, run autoflake to automatically fix issues
    if fix:
        logger.info("Applying automatic fixes with autoflake")
        fix_cmd = [
            "uv",
            "run",
            "autoflake",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--recursive",
            "--in-place",
            "--ignore-init-module-imports",
        ]

        # Always add a file path, use "." for the current directory if not specified
        if file_path != ".":
            fix_cmd.append(file_path)
        else:
            fix_cmd.append(".")

        # Add debug logging to print the exact command
        logger.info(f"DEBUG - Running command: {' '.join(fix_cmd)}")
        logger.info(f"DEBUG - Current working directory: {str(git_root)}")

        logger.debug(f"Running fix command: {' '.join(fix_cmd)}")
        fix_result = subprocess.run(
            fix_cmd, cwd=str(git_root), text=True, capture_output=True
        )

        # Add debug logging to print the result
        logger.info(f"DEBUG - Command exit code: {fix_result.returncode}")
        logger.info(f"DEBUG - Command stdout: {fix_result.stdout}")
        logger.info(f"DEBUG - Command stderr: {fix_result.stderr}")

        if fix_result.returncode != 0:
            logger.error(f"Autoflake fix failed: {fix_result.stderr}")
            return {
                "Status": "Error",
                "Message": f"Autoflake fix failed with error: {fix_result.stderr}",
                "Instructions": (
                    "There was an error running autoflake. Please check if autoflake "
                    "is installed correctly and that the file path is valid."
                ),
            }

        logger.info("Autoflake fixes applied successfully")

    # Delete any existing autoflake.json file to prevent appenåding issues
    autoflake_report = git_root / "reports/autoflake.json"
    if autoflake_report.exists():
        autoflake_report.unlink()
        logger.info(f"Deleted existing report file: {autoflake_report}")

    # Run flake8 to generate a report of any remaining issues
    flake8_cmd = [
        "uv",
        "run",
        "flake8",
        "--format=json",
        "--output-file=./reports/autoflake.json",
        "--max-line-length=89",
        "--ignore=E203,W503",  # Ignore whitespace before colon
        "--exclude=*cookiecutter*,*decorators.py",  # Exclude cookiecutter templates
        # and decorators.py
        "--select=F401,F841",  # Select only unused imports (F401)
        # and unused variables (F841)
    ]

    if file_path != ".":
        flake8_cmd.append(file_path)
    else:
        flake8_cmd.append(".")

    # Log the actual command with resolved paths
    resolved_cmd = " ".join([str(arg) for arg in flake8_cmd])
    logger.debug(f"Running flake8 command: {resolved_cmd}")

    flake8_result = subprocess.run(
        flake8_cmd, cwd=str(git_root), text=True, capture_output=True
    )

    if (
        flake8_result.returncode != 0
        and "No such file or directory" in flake8_result.stderr
    ):
        logger.error(f"Flake8 failed: {flake8_result.stderr}")
        return {
            "Status": "Error",
            "Message": f"Flake8 failed with error: {flake8_result.stderr}",
            "Instructions": (
                "There was an error running flake8. Please check if flake8 "
                "is installed correctly and that the file path is valid."
            ),
        }

    time.sleep(1)  # Give time for file system operations to complete

    # Process the results
    autoflake_results = process_autoflake_results(git_root / "reports/autoflake.json")

    # Check if there are any issues
    if autoflake_results.get("Status") == "Issues Found":
        logger.warning(f"Autoflake issues found: {autoflake_results.get('Issue')}")
        return {
            "Status": "Issues Found",
            "Issue": autoflake_results.get("Issue"),
            "Instructions": (
                "Let's fix the issue in the file. After fixing this issue, run the "
                "run_autoflake tool again to check for more issues. If you want to "
                "automatically fix all issues, you can run the tool with fix=False."
            ),
        }

    # If no issues, return success
    logger.info("No autoflake issues found")
    return {
        "Status": "Success",
        "Message": "Great job! Your code is clean with no unused imports or variables.",
        "Instructions": (
            "Your code is looking great! You might want to run other code quality tools "
            "like isort or black next to ensure your code is well-formatted."
        ),
    }


if __name__ == "__main__":  # pragma: no cover
    # Print service information
    logger.info("Starting pytest MCP server")

    # Run the MCP server
    try:
        mcp.settings.port = 8081
        mcp.run(transport="sse")
    except Exception as e:
        logger.exception(f"Error running MCP server: {e}")
