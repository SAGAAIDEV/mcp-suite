"""
Flake8 tool for the SaagaLint MCP server.

This module provides a tool for checking code style and quality using flake8.
It integrates with the MCP server to provide a unified interface for code
quality checks.

Features:
- Check code style and quality using flake8
- Generate JSON reports of issues
- Provide helpful instructions for fixing issues
- Integration with the existing autoflake processing
"""

import subprocess

from mcp_suite.servers.qa.service.flake8 import process_flake8_results
from mcp_suite.servers.qa.utils.decorators import exception_handler
from mcp_suite.servers.qa.utils.git_utils import get_git_root


@exception_handler()
async def run_flake8(
    file_path: str = ".", max_line_length: int = 89, ignore: str = "E203,W503"
):
    """
    Run flake8 analysis on specified files or directories.

    This function checks code style and quality using flake8 and generates
    a JSON report that can be processed by the existing autoflake processing.

    Args:
        file_path: Path to the file or directory to analyze (relative to git root)
                  Defaults to current directory if not specified
        max_line_length: Maximum line length (default: 89)
        ignore: Comma-separated list of error codes to ignore (default: "E203,W503")

    Returns:
        dict: A dictionary containing analysis results and instructions
    """
    # Find git root directory
    git_root = get_git_root()

    # Ensure reports directory exists
    reports_dir = git_root / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Define the output file path
    output_file = git_root / "flake8.json"

    # Delete any existing flake8.json file to prevent appending issues
    if output_file.exists():
        output_file.unlink()

    # Prepare the command
    cmd = [
        "uv",
        "run",
        "flake8",
        "--format=json",
        f"--output-file={output_file}",
        f"--max-line-length={max_line_length}",
        f"--ignore={ignore}",
        "--exclude=*cookiecutter*",
    ]

    # Add the target file or directory
    if file_path != ".":
        cmd.append(file_path)
    else:
        cmd.append(".")

    # Run the command
    result = subprocess.run(cmd, cwd=str(git_root), text=True, capture_output=True)

    # Check if flake8 ran successfully
    if result.returncode != 0 and "No such file or directory" in result.stderr:
        return {
            "Status": "Error",
            "Message": f"Flake8 failed with error: {result.stderr}",
            "Instructions": (
                "There was an error running flake8. Please check if flake8 "
                "is installed correctly and that the file path is valid."
            ),
        }

    # Process the results using the existing autoflake processing
    return process_flake8_results(output_file)
