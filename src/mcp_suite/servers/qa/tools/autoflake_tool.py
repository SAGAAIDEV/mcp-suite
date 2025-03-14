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
"""

import subprocess
import time

from mcp_suite.servers.qa import logger as main_logger
from mcp_suite.servers.qa.service.autoflake import (
    process_autoflake_results,
)
from mcp_suite.servers.qa.utils.decorators import exception_handler
from mcp_suite.servers.qa.utils.git_utils import get_git_root
from mcp_suite.servers.qa.utils.logging_utils import get_component_logger

# Get a component-specific logger
logger = get_component_logger("autoflake")


@exception_handler()
async def run_autoflake(file_path: str = ".", fix: bool = True):
    """
    Run autoflake analysis on specified files or directories.

    This function detects unused imports and variables in Python code
    and can automatically fix them if requested.

    Args:
        file_path: Path to the file or directory to analyze (relative to git root)
                  Defaults to current directory if not specified
        fix: Boolean flag to automatically apply fixes (default: True)

    Returns:
        dict: A dictionary containing analysis results and instructions
    """
    logger.info(f"Running autoflake on: {file_path} with fix={fix}")
    main_logger.info(f"Running autoflake on: {file_path} with fix={fix}")

    # Find git root directory
    git_root = get_git_root()
    logger.debug(f"Git root directory: {git_root}")

    reports_dir = git_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    logger.debug(f"Reports directory: {reports_dir}")

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
        logger.debug(f"Running command: {' '.join(fix_cmd)}")
        logger.debug(f"Current working directory: {str(git_root)}")

        fix_result = subprocess.run(
            fix_cmd, cwd=str(git_root), text=True, capture_output=True
        )

        # Add debug logging to print the result
        logger.debug(f"Command exit code: {fix_result.returncode}")
        logger.debug(f"Command stdout: {fix_result.stdout}")

        if fix_result.stderr:
            logger.warning(f"Command stderr: {fix_result.stderr}")

        if fix_result.returncode != 0:
            error_msg = f"Autoflake fix failed: {fix_result.stderr}"
            logger.error(error_msg)
            main_logger.error(error_msg)

            return {
                "Status": "Error",
                "Message": f"Autoflake fix failed with error: {fix_result.stderr}",
                "Instructions": (
                    "There was an error running autoflake. Please check if autoflake "
                    "is installed correctly and that the file path is valid."
                ),
            }

        logger.info("Autoflake fixes applied successfully")

    # Delete any existing autoflake.json file to prevent appending issues
    autoflake_report = git_root / "reports/autoflake.json"
    if autoflake_report.exists():
        autoflake_report.unlink()
        logger.info(f"Deleted existing report file: {autoflake_report}")

    # Run flake8 to generate a report of any remaining issues
    logger.info("Running flake8 to check for remaining issues")
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

    logger.debug(f"Flake8 exit code: {flake8_result.returncode}")
    logger.debug(f"Flake8 stdout: {flake8_result.stdout}")

    if flake8_result.stderr:
        logger.warning(f"Flake8 stderr: {flake8_result.stderr}")

    if (
        flake8_result.returncode != 0
        and "No such file or directory" in flake8_result.stderr
    ):
        error_msg = f"Flake8 failed: {flake8_result.stderr}"
        logger.error(error_msg)
        main_logger.error(error_msg)

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
    logger.info("Processing autoflake results")
    autoflake_results = process_autoflake_results(git_root / "reports/autoflake.json")
    logger.debug(f"Processed results: {autoflake_results}")

    # Check if there are any issues
    if autoflake_results.get("Status") == "Issues Found":
        issue = autoflake_results.get("Issue")
        logger.warning(f"Autoflake issues found: {issue}")
        main_logger.warning(f"Autoflake issues found: {issue}")

        return {
            "Status": "Issues Found",
            "Issue": issue,
            "Instructions": (
                "Let's fix the issue in the file. After fixing this issue, run the "
                "run_autoflake tool again to check for more issues. If you want to "
                "automatically fix all issues, you can run the tool with fix=False."
            ),
        }

    # If no issues, return success
    logger.info("No autoflake issues found")
    main_logger.info("Autoflake analysis complete - no issues found")

    return {
        "Status": "Success",
        "Message": "Great job! Your code is clean with no unused imports or variables.",
        "Instructions": (
            "Your code is looking great! You might want to run other code quality tools "
            "like isort or black next to ensure your code is well-formatted."
        ),
    }
