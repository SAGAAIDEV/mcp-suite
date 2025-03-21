"""
Flake8 library module for the SaagaLint MCP server.

This module provides utility functions for running flake8 on Python code
and processing the results.

Functions:
- set_output_file: Set up the output file path for flake8 results
- run_flake8_command: Run the flake8 command on a file or directory
- process_flake8_issues: Process the flake8 results into a list of dictionaries
- get_next_flake8_issue: Get the next flake8 issue to fix
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from mcp_suite.servers.qa.config import logger


def set_output_file(git_root: Path) -> Path:
    """
    Set up the output file path for flake8 results.

    Args:
        git_root: Path to the git root directory

    Returns:
        Path: Path to the output file
    """
    reports_dir = git_root / "reports"
    logger.debug(f"Reports directory: {reports_dir}")
    reports_dir.mkdir(exist_ok=True)

    output_file = reports_dir / "flake8.json"
    logger.debug(f"Output file: {output_file}")

    if output_file.exists():
        logger.debug("Removing existing flake8.json file")
        output_file.unlink()

    return output_file


def run_flake8_command(
    file_path: str,
    output_file: Path,
    git_root: Path,
    max_line_length: int = 89,
    ignore: str = "E203,W503",
) -> Tuple[bool, str]:
    """
    Run the flake8 command on a file or directory.

    Args:
        file_path: Path to the file or directory to analyze
        output_file: Path to the output file
        git_root: Path to the git root directory
        max_line_length: Maximum line length for flake8
        ignore: Comma-separated list of error codes to ignore

    Returns:
        Tuple[bool, str]: Success status and error message (if any)
    """
    logger.info(f"Running flake8 on {file_path}")

    cmd = [
        "flake8",
        "--format=json",
        f"--output-file={output_file}",
        f"--max-line-length={max_line_length}",
        f"--ignore={ignore}",
        file_path,
    ]

    logger.debug(f"Running command: {' '.join(cmd)}")

    try:
        process = subprocess.run(
            cmd,
            cwd=git_root,
            check=False,
            capture_output=True,
            text=True,
        )

        logger.debug(f"Flake8 exit code: {process.returncode}")

        if process.returncode != 0:
            error_message = f"Flake8 failed with error: {process.stderr}"
            logger.error(error_message)
            return False, error_message
        return True, ""
    except Exception as e:
        error_message = f"Error running flake8: {str(e)}"
        logger.error(error_message)
        return False, error_message


def process_flake8_issues(report_file: Union[Path, str]) -> List[Dict]:
    """
    Process the flake8 results.

    Args:
        report_file: Path to the flake8 report file

    Returns:
        List[Dict]: List of flake8 issues as dictionaries
    """
    logger.info(f"Processing flake8 issues from {report_file}")

    # Convert string to Path if needed
    if isinstance(report_file, str):
        report_file = Path(report_file)

    if not report_file.exists():
        logger.warning(f"Flake8 report file not found: {report_file}")
        return []

    try:
        with open(report_file, "r") as f:
            data = json.load(f)

        all_issues = []

        for file_path, issues in data.items():
            for issue in issues:
                all_issues.append(issue)

        logger.info(f"Found {len(all_issues)} flake8 issues")
        return all_issues

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {report_file}: {str(e)}")
        # Return empty list instead of raising
        return []
    except Exception as e:
        logger.exception(f"Error processing flake8 issues: {str(e)}")
        raise


def get_next_flake8_issue(report_file: Path) -> Optional[Dict]:
    """
    Get the next flake8 issue to fix.

    Args:
        report_file: Path to the flake8 report file

    Returns:
        Optional[Dict]: The next flake8 issue to fix, or None if no issues
    """
    logger.info("Getting next flake8 issue")

    all_issues = process_flake8_issues(report_file)

    try:
        return all_issues[0] if all_issues else None
    except IndexError:
        logger.info("No more flake8 issues to fix")
        return None


def process_flake8_results(report_file: Union[Path, str]) -> List[Dict]:
    """
    Alias for process_flake8_issues for backward compatibility.

    Args:
        report_file: Path to the flake8 report file

    Returns:
        List[Dict]: List of flake8 issues as dictionaries

    Raises:
        FileExistsError: If the report file doesn't exist
    """
    # Convert string to Path if needed
    if isinstance(report_file, str):
        report_file = Path(report_file)

    # Check if file exists
    if not report_file.exists():
        error_msg = f"Flake8 report file not found: {report_file}"
        logger.error(error_msg)
        raise FileExistsError(error_msg)

    return process_flake8_issues(report_file)
