"""
Pytest runner utilities.

This module provides functions for running pytest tests and generating reports.
It handles the execution of pytest with coverage and the generation of JSON reports.
"""

import subprocess
import sys
from pathlib import Path

from loguru import logger

from mcp_suite.servers.qa.config.constants import ReportPaths
from mcp_suite.servers.qa.models.tool_result import NextAction, ToolResult, ToolStatus
from mcp_suite.servers.qa.utils.git_utils import get_git_root

# Create a logger specifically for pytest runner
pytest_runner_logger = logger.bind(component="pytest_runner")


def prepare_reports():
    """
    Prepare report directories and clean old reports.

    Returns:
        tuple: (pytest_report_path, coverage_report_path) - Paths to the report files
    """
    git_root = get_git_root()
    pytest_runner_logger.debug(f"Git root directory: {git_root}")

    # Delete old report files if they exist
    pytest_report_path = Path(ReportPaths.PYTEST_RESULTS)
    coverage_report_path = Path(ReportPaths.COVERAGE)

    if pytest_report_path.exists():
        pytest_runner_logger.debug(f"Deleting old pytest report: {pytest_report_path}")
        pytest_report_path.unlink()

    if coverage_report_path.exists():
        pytest_runner_logger.debug(
            f"Deleting old coverage report: {coverage_report_path}"
        )
        coverage_report_path.unlink()

    # Ensure reports directory exists
    reports_dir = git_root / "reports"
    if not reports_dir.exists():
        pytest_runner_logger.debug(f"Creating reports directory: {reports_dir}")
        reports_dir.mkdir(parents=True, exist_ok=True)

    return pytest_report_path, coverage_report_path


def run_pytest_with_coverage(
    file_path: str,
    pytest_report_path: Path,
    coverage_report_path: Path,
    tool_function,
) -> ToolResult:
    """
    Run pytest with coverage using subprocess and generate reports.

    Args:
        file_path: Path to the file or directory to test
        pytest_report_path: Path to write pytest report
        coverage_report_path: Path to write coverage report
        tool_function: The function to reference in the NextAction

    Returns:
        ToolResult: Error result if execution fails, None otherwise
    """
    git_root = get_git_root()
    pytest_runner_logger.debug(f"Git root directory: {git_root}")

    # Prepare command to run pytest with coverage and JSON reporting
    # coverage src is specified in pyproject.toml
    # I think this will have to be set to manage file size in the future
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        file_path,
        "--json-report",
        f"--json-report-file={pytest_report_path}",
        "--cov",
        f"--cov-report=json:{coverage_report_path}",
    ]

    # Log the command being executed
    pytest_runner_logger.info(f"Running command: {' '.join(cmd)}")

    try:
        # Run pytest with subprocess
        result = subprocess.run(
            cmd,
            cwd=git_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        # Log the command output
        pytest_runner_logger.debug(f"Command stdout: {result.stdout}")
        pytest_runner_logger.debug(f"Command stderr: {result.stderr}")
        pytest_runner_logger.debug(f"Return code: {result.returncode}")

        # Check if report files were created
        if not pytest_report_path.exists():
            pytest_runner_logger.error("Pytest report file was not created")
            next_action = NextAction(
                tool=tool_function,
                instructions="Try running pytest again with the same parameters.",
            )
            return ToolResult(
                status=ToolStatus.ERROR,
                message="Pytest report file was not created",
                next_action=next_action,
            )

        # Check if coverage report was generated
        if not coverage_report_path.exists():
            pytest_runner_logger.warning("No coverage data was collected")
            # We'll continue without coverage data instead of returning an error

        # Return None if everything went well (no error)
        return None

    except (
        subprocess.SubprocessError,
        FileNotFoundError,
        PermissionError,
        OSError,
    ) as e:
        pytest_runner_logger.error(f"Error running pytest subprocess: {str(e)}")
        next_action = NextAction(
            tool=tool_function,
            instructions="Try running pytest again with the same parameters.",
        )
        return ToolResult(
            status=ToolStatus.ERROR,
            message=f"Error running pytest: {str(e)}",
            next_action=next_action,
        )
