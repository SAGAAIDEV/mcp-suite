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

from mcp_suite.servers.qa import logger
from mcp_suite.servers.qa.utils.decorators import exception_handler
from mcp_suite.servers.qa.utils.git_utils import get_git_root


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
    logger.info(f"Running autoflake on {file_path} with fix={fix}")

    # Find git root directory
    git_root = get_git_root()
    logger.debug(f"Git root directory: {git_root}")

    # Prepare the command
    cmd = [
        "uv",
        "run",
        "autoflake",
        "--recursive",
        "--remove-all-unused-imports",
        "--remove-unused-variables",
        "--remove-duplicate-keys",
        "--expand-star-imports",
        "--ignore-init-module-imports",
        "--quiet",
    ]

    # Add fix flag if requested
    if fix:
        cmd.append("--in-place")
        logger.debug("Running in fix mode (--in-place)")
    else:
        logger.debug("Running in check mode (no --in-place)")

    # Add the target file or directory
    cmd.append(file_path)

    # Run the command
    logger.info(f"Executing command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(git_root), text=True, capture_output=True)
    logger.debug(f"Command exit code: {result.returncode}")

    # Process the results
    if result.returncode == 0:
        logger.info("Autoflake analysis completed successfully")
        return {
            "Status": "Success",
            "Message": "Autoflake analysis completed successfully.",
            "Instructions": (
                "Great job! Your code is clean and free of unused imports "
                "and variables. Keep up the good work!"
            ),
        }
    else:
        logger.error(f"Autoflake analysis failed with exit code {result.returncode}")
        logger.error(f"Error: {result.stderr}")
        return {
            "Status": "Error",
            "Message": f"Autoflake analysis failed with exit code {result.returncode}",
            "Error": result.stderr,
            "Instructions": (
                "Let's fix these issues together. I'll help you understand what's wrong "
                "and how to fix it. Once you've made the changes, run the autoflake "
                "tool again to verify the fixes."
            ),
        }
