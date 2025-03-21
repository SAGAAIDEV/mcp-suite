"""
Isort service for the SaagaLint MCP server.

This module provides functionality for running isort to automatically fix
import ordering in Python code.
"""

import subprocess
from pathlib import Path

from mcp_suite.servers.qa.config import logger


def run_isort(
    file_path: str, git_root: Path, max_line_length: int = 89
) -> subprocess.CompletedProcess:
    """
    Run isort to fix import ordering.

    Args:
        file_path: Path to the file or directory to analyze (relative to git root)
        git_root: Path to the git root directory
        max_line_length: Maximum line length (default: 89)

    Returns:
        subprocess.CompletedProcess: Result of the isort command

    Raises:
        RuntimeError: If isort fails with a non-zero exit code
    """
    logger.info(f"Running isort on {file_path} to fix import ordering")

    # Prepare the command
    isort_cmd = [
        "uv",
        "run",
        "isort",
        "--profile",
        "black",
        f"--line-length={max_line_length}",
    ]

    # Add the target file or directory for isort
    if file_path != ".":
        isort_cmd.append(file_path)
    else:
        isort_cmd.append(".")

    logger.debug(f"Executing isort command: {' '.join(isort_cmd)}")
    isort_result = subprocess.run(
        isort_cmd, cwd=str(git_root), text=True, capture_output=True
    )
    logger.debug(f"Isort exit code: {isort_result.returncode}")

    # Log stdout and stderr
    if isort_result.stdout:
        logger.debug(f"Isort stdout: {isort_result.stdout}")
    if isort_result.stderr:
        logger.error(f"Isort stderr: {isort_result.stderr}")

    # Raise exception if isort failed
    if isort_result.returncode != 0:
        error_msg = f"Isort failed with exit code {isort_result.returncode}"
        if isort_result.stderr:
            error_msg += f": {isort_result.stderr}"
        raise RuntimeError(error_msg)

    return isort_result
