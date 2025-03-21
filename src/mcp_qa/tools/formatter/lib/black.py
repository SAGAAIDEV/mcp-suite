"""
Black service for the SaagaLint MCP server.

This module provides functionality for running black to automatically format
Python code according to PEP 8 style guidelines.
"""

import subprocess
from pathlib import Path

from mcp_qa.config import logger


def run_black(
    file_path: str, git_root: Path, max_line_length: int = 89
) -> subprocess.CompletedProcess:
    """
    Run black to fix formatting and long lines.

    Args:
        file_path: Path to the file or directory to format (relative to git root)
        git_root: Path to the git root directory
        max_line_length: Maximum line length (default: 89)

    Returns:
        subprocess.CompletedProcess: Result of the black command

    Raises:
        RuntimeError: If black fails with a non-zero exit code
    """
    logger.info(f"Running black on {file_path} to fix formatting and long lines")

    # Prepare the command
    black_cmd = [
        "uv",
        "run",
        "black",
        f"--line-length={max_line_length}",
    ]

    # Add the target file or directory for black
    if file_path != ".":
        black_cmd.append(file_path)
    else:
        black_cmd.append(".")

    logger.debug(f"Executing black command: {' '.join(black_cmd)}")
    black_result = subprocess.run(
        black_cmd, cwd=str(git_root), text=True, capture_output=True
    )
    logger.debug(f"Black exit code: {black_result.returncode}")

    # Log stdout and stderr
    if black_result.stdout:
        logger.debug(f"Black stdout: {black_result.stdout}")
    if black_result.stderr:
        logger.error(f"Black stderr: {black_result.stderr}")

    # Raise exception if black failed
    if black_result.returncode != 0:
        error_msg = f"Black failed with exit code {black_result.returncode}"
        if black_result.stderr:
            error_msg += f": {black_result.stderr}"
        raise RuntimeError(error_msg)

    return black_result
