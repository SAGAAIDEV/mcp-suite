"""
Pytest reporting tool for the SaagaLint MCP server.

This module provides functionality for running pytest tests and generating
comprehensive reports across the entire codebase. It integrates with the MCP
server to provide a unified interface for running tests, analyzing results,
and reporting coverage metrics.

Features:
- Run pytest tests on specified files or across the entire codebase
- Generate detailed JSON reports for test results
- Track and analyze code coverage metrics
- Identify test failures and collection errors
- Provide actionable feedback for resolving test issues
- Generate coverage summaries for the entire codebase
"""

import argparse
import asyncio
import json
import os
import traceback
from typing import Any, Dict

from mcp_suite.servers.qa.config import logger as pytest_logger
from mcp_suite.servers.qa.models.tool_result import NextAction, ToolResult, ToolStatus
from mcp_suite.servers.qa.tools.testing.coverage_report import run_coverage
from mcp_suite.servers.qa.tools.testing.lib.pytest_runner import (
    prepare_reports,
    run_pytest_with_coverage,
)
from mcp_suite.servers.qa.tools.testing.lib.result_processor import process_test_results


async def generate_test_reports(file_path: str = "/src"):
    """
    Run pytest tests across the codebase and generate comprehensive reports.

    This function runs pytest from the git root directory to execute tests and
    generate detailed reports on test results and code coverage. It can target
    specific files or the entire codebase, providing insights into test status
    and coverage metrics.

    Args:
        file_path: Path to the file or directory to test (relative to git root)
                  Examples:
                  - "src/mcp_suite/base/redis_db/tests/test_redis_manager.py"
                    for a specific test
                  - "src/mcp_suite" for all tests in a module
                  - "." for all tests in the entire codebase

    Returns:
        ToolResult: A ToolResult object containing test results, coverage metrics,
                  and remediation instructions
    """
    # Pass in the file that we want to test
    #
    try:

        pytest_logger.info(f"Starting pytest run with file_path={file_path}")

        # 1. Validate inputs
        pytest_logger.debug("Step 1: Validating file path")
        # validation_result = validate_file_path(file_path, run_pytest)
        # if validation_result:
        #     pytest_logger.warning(
        #         f"File path validation failed: {validation_result.message}"
        #     )
        #     return validation_result

        # 2. Prepare report paths
        pytest_logger.debug("Step 2: Preparing report paths")
        pytest_report_path, coverage_report_path = prepare_reports()
        pytest_logger.info(
            f"Report paths: pytest={pytest_report_path}, coverage={coverage_report_path}"
        )

        # 3. Run pytest and generate reports using subprocess
        pytest_logger.info("Step 3: Running pytest with coverage")
        error_result = run_pytest_with_coverage(
            file_path,
            pytest_report_path,
            coverage_report_path,
            generate_test_reports,
        )
        if error_result:
            pytest_logger.warning(f"Pytest execution failed: {error_result.message}")
            return error_result
        pytest_logger.info("Pytest execution completed successfully")

        # 4. Process test results
        pytest_logger.info("Step 4: Processing test results")
        test_result = process_test_results_and_coverage(
            pytest_report_path, coverage_report_path
        )

        return test_result

    except (FileNotFoundError, PermissionError) as e:
        pytest_logger.error(f"File system error: {str(e)}")
        return ToolResult(
            status=ToolStatus.ERROR,
            message=f"File system error: {str(e)}",
        )
    except json.JSONDecodeError as e:
        pytest_logger.error(f"JSON parsing error: {str(e)}")
        return ToolResult(
            status=ToolStatus.ERROR,
            message=f"Error parsing JSON: {str(e)}",
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        pytest_logger.error(f"Error in run_pytest: {str(e)}")
        pytest_logger.error(f"Exception traceback: {traceback.format_exc()}")
        return ToolResult(
            status=ToolStatus.ERROR,
            message=f"Error running pytest: {str(e)}",
        )


def load_pytest_report(pytest_report_path: str) -> tuple[dict | None, str | None]:
    """
    Load and process the pytest report from the specified path.

    Args:
        pytest_report_path: Path to the pytest JSON report

    Returns:
        tuple: (report_data, error_message)
              report_data is None if there was an error
              error_message is None if loading was successful
    """
    if not os.path.exists(pytest_report_path):
        pytest_logger.error("Pytest report file does not exist")
        return None, "Pytest report file does not exist"

    try:
        with open(pytest_report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
            return report_data, None
    except json.JSONDecodeError:
        pytest_logger.error("Failed to parse pytest JSON report")
        return None, "Failed to parse pytest JSON report"


def load_coverage_report(coverage_report_path: str) -> dict | None:
    """
    Load the coverage report from the specified path.

    Args:
        coverage_report_path: Path to the coverage JSON report

    Returns:
        dict or None: The coverage data, or None if loading failed
    """
    if not os.path.exists(coverage_report_path):
        return None

    try:
        with open(coverage_report_path, "r", encoding="utf-8") as f:
            coverage_data = json.load(f)
        pytest_logger.debug("Coverage data loaded successfully")
        return coverage_data
    except json.JSONDecodeError:
        pytest_logger.warning("Failed to parse coverage JSON report")
        return None


def create_success_result(coverage_data: dict | None) -> ToolResult:
    """
    Create a success result with coverage information.

    Args:
        coverage_data: The coverage data from the JSON report

    Returns:
        ToolResult: A success result with coverage information
    """
    pytest_logger.info("All tests passed successfully")

    # Add coverage information to the message
    coverage_info = (
        extract_coverage_summary(coverage_data)
        if coverage_data
        else "No coverage data available"
    )

    next_action = NextAction(
        tool=run_coverage,
        instructions="Run mcp tool analysis to check code coverage.",
    )

    return ToolResult(
        status=ToolStatus.SUCCESS,
        message=(
            "All tests passed successfully! No errors or failures detected.\n\n"
            f"Coverage Summary:\n{coverage_info}"
        ),
        next_action=next_action,
    )


def create_failure_result(test_error: str) -> ToolResult:
    """
    Create a failure result with test error information.

    Args:
        test_error: The error message from test results

    Returns:
        ToolResult: A failure result with error information
    """
    pytest_logger.warning(f"Test failures or errors detected: {test_error}")

    next_action = NextAction(
        tool=generate_test_reports,
        instructions="1. Fix the error. 2. Then run the mcp tool again.",
    )

    return ToolResult(
        status=ToolStatus.FAILURE,
        message=f"Test failures or errors detected: {test_error}",
        next_action=next_action,
    )


def process_test_results_and_coverage(
    pytest_report_path: str,
    coverage_report_path: str,
) -> ToolResult:
    """
    Process pytest results and coverage data for the codebase.

    This function analyzes the JSON reports generated by pytest and coverage tools,
    extracting key information about test successes, failures, and code coverage
    metrics. It generates a comprehensive summary and recommends next actions
    based on results.

    Args:
        pytest_report_path: Path to the pytest JSON report
        coverage_report_path: Path to the coverage JSON report

    Returns:
        ToolResult: Consolidated results with test status, coverage metrics,
                  and recommended actions
    """
    # Load and process pytest report
    report_data, error_message = load_pytest_report(pytest_report_path)
    if error_message:
        return ToolResult(
            status=ToolStatus.ERROR,
            message=error_message,
        )

    # Process test results
    test_error = process_test_results(report_data, generate_test_reports)
    pytest_logger.debug(f"Test result processing completed, error={test_error}")

    # Load coverage data
    coverage_data = load_coverage_report(coverage_report_path)

    # Create appropriate result based on test outcome
    if test_error is None:
        return create_success_result(coverage_data)
    else:
        return create_failure_result(test_error)


def extract_coverage_summary(coverage_data: Dict[str, Any]) -> str:
    """
    Extract and format a comprehensive coverage summary for the codebase.

    This function processes raw coverage data and generates a human-readable summary
    that includes overall coverage metrics and highlights the top performing files.
    The summary provides a quick assessment of code test coverage across the codebase.

    Args:
        coverage_data: Coverage data dictionary from the JSON report

    Returns:
        str: Formatted coverage summary with overall metrics and top file details
    """
    if not coverage_data or "totals" not in coverage_data:
        return "No coverage data available"

    totals = coverage_data["totals"]

    summary_lines = [
        f"Total Coverage: {totals.get('percent_covered', 0):.2f}%",
        (
            f"Lines Covered: {totals.get('covered_lines', 0)} "
            f"of {totals.get('num_statements', 0)}"
        ),
    ]

    if "files" in coverage_data and coverage_data["files"]:
        summary_lines.append("\nTop files by coverage:")
        file_items = list(coverage_data["files"].items())
        # Sort by coverage percentage (descending)
        file_items.sort(
            key=lambda x: x[1].get("summary", {}).get("percent_covered", 0),
            reverse=True,
        )

        # Show top 5 files
        for i, (file_path, file_data) in enumerate(file_items[:5]):
            percent = file_data.get("summary", {}).get("percent_covered", 0)
            covered = file_data.get("summary", {}).get("covered_lines", 0)
            total = file_data.get("summary", {}).get("num_statements", 0)
            summary_lines.append(
                f"{i + 1}. {file_path}: {percent:.2f}% ({covered}/{total} lines)"
            )

    return "\n".join(summary_lines)


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Run pytest tests and generate reports"
    )
    parser.add_argument("file_path", help="Path to the file or directory to test")
    args = parser.parse_args()

    result = asyncio.run(generate_test_reports(args.file_path))

    # Pretty print the result
    print(json.dumps(result, indent=2, default=str))
