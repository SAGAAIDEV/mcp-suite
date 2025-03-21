"""
Autoflake service for the SaagaLint MCP server.

This module provides functionality for running autoflake to automatically fix
common issues in Python code, such as removing unused imports and variables.
"""

import subprocess
from pathlib import Path

from mcp_qa.config import logger


def run_autoflake(file_path: str, git_root: Path) -> subprocess.CompletedProcess:
    """
    Run autoflake to fix unused imports and variables.

    Args:
        file_path: Path to the file or directory to analyze (relative to git root)
        git_root: Path to the git root directory

    Returns:
        subprocess.CompletedProcess: Result of the autoflake command

    Raises:
        RuntimeError: If autoflake fails with a non-zero exit code
    """
    logger.info(f"Running autoflake on {file_path} to fix issues automatically")

    # Prepare the command
    autoflake_cmd = [
        "uv",
        "run",
        "autoflake",
        "--in-place",
        "--recursive",
        "--remove-all-unused-imports",
        "--remove-unused-variables",
        "--remove-duplicate-keys",
        "--expand-star-imports",
        "--ignore-init-module-imports",
        "--quiet",
    ]

    # Add the target file or directory for autoflake
    if file_path != ".":
        autoflake_cmd.append(file_path)
    else:
        autoflake_cmd.append(".")

    logger.debug(f"Executing autoflake command: {' '.join(autoflake_cmd)}")
    autoflake_result = subprocess.run(
        autoflake_cmd, cwd=str(git_root), text=True, capture_output=True
    )
    logger.debug(f"Autoflake exit code: {autoflake_result.returncode}")

    # Log stdout and stderr
    if autoflake_result.stdout:
        logger.debug(f"Autoflake stdout: {autoflake_result.stdout}")
    if autoflake_result.stderr:
        logger.error(f"Autoflake stderr: {autoflake_result.stderr}")

    # Raise exception if autoflake failed
    if autoflake_result.returncode != 0:
        error_msg = f"Autoflake failed with exit code {autoflake_result.returncode}"
        if autoflake_result.stderr:
            error_msg += f": {autoflake_result.stderr}"
        raise RuntimeError(error_msg)

    return autoflake_result
