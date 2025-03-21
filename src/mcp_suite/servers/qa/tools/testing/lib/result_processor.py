"""
Result processor utilities for pytest.

This module provides functions for processing pytest results and extracting
information about test failures and collection errors.
"""

from pathlib import Path
from typing import Dict, Union

from loguru import logger

from mcp_suite.servers.qa.models.tool_result import NextAction, ToolResult, ToolStatus
from mcp_suite.servers.qa.tools.testing.lib.pytest import process_pytest_results

# Create a logger specifically for result processing
result_logger = logger.bind(component="pytest_results")


def process_test_results(pytest_report: Union[Path, Dict, str], tool_function):
    """
    Process pytest results and check for errors or failures.

    Args:
        pytest_report: Path to the pytest report file or the report data dictionary
        tool_function: The function to reference in the NextAction

    Returns:
        dict or None: Returns error details or None if all tests passed
    """
    # Process the results to get both collection errors and test failures
    result_logger.info("Processing pytest results")

    # Handle different input types
    if isinstance(pytest_report, dict):
        # Direct processing of the data dictionary
        result_logger.debug("Processing pytest results from dictionary")
        processed_results = process_pytest_data(pytest_report)
    else:
        # Process from file path
        result_logger.debug(f"Processing pytest results from file: {pytest_report}")
        processed_results = process_pytest_results(str(pytest_report))

    # Check for collection errors first
    if processed_results.failed_collections:
        return processed_results.failed_collections[0].model_dump()

    # If no collection errors, check for test failures
    if processed_results.failed_tests:
        return processed_results.failed_tests[0].model_dump()

    # If no failures of any kind, return None
    result_logger.info("All tests passed successfully!")
    return None


def process_pytest_data(data: Dict):
    """
    Process pytest results directly from a data dictionary.

    This is a wrapper around process_pytest_results that handles dictionary input.

    Args:
        data: The pytest results data dictionary

    Returns:
        PytestResults object containing summary, failed collections, and failed tests
    """
    from mcp_suite.servers.qa.tools.testing.models.pytest_models import (
        PytestCollectionFailure,
        PytestFailedTest,
        PytestResults,
        PytestSummary,
    )

    result_logger.debug("Processing pytest data dictionary")

    # Ensure tests key exists
    if "tests" not in data:
        error_msg = "Error: 'tests' key not found in data"
        result_logger.error(error_msg)
        return PytestResults(summary=PytestSummary(), error=error_msg)

    # Extract failed collections
    failed_collections = []
    if "collectors" in data:
        result_logger.debug("Processing collection errors")
        # Handle both formats: list of collectors or dict with errors key
        if isinstance(data["collectors"], list):
            for collector in data["collectors"]:
                if collector.get("outcome") == "failed":
                    failed_collections.append(
                        PytestCollectionFailure(
                            nodeid=collector.get("nodeid", "Unknown"),
                            outcome=collector.get("outcome", "failed"),
                            longrepr=collector.get("longrepr", "Unknown error"),
                        )
                    )
        elif isinstance(data["collectors"], dict) and "errors" in data["collectors"]:
            for error in data["collectors"]["errors"]:
                failed_collections.append(
                    PytestCollectionFailure(
                        nodeid=error.get("nodeid", "Unknown"),
                        outcome="failed",
                        longrepr=error.get("longrepr", "Unknown error"),
                    )
                )
        if failed_collections:
            result_logger.warning(f"Found {len(failed_collections)} collection errors")

    # Extract failed tests
    failed_tests = []
    if "tests" in data:
        result_logger.debug("Processing test failures")
        for test in data["tests"]:
            if test.get("outcome") == "failed":
                failed_tests.append(
                    PytestFailedTest(
                        nodeid=test.get("nodeid", "Unknown"),
                        outcome=test.get("outcome", "Unknown"),
                        longrepr=test.get("longrepr", None),
                        duration=test.get("duration", None),
                        lineno=test.get("lineno", 0),
                        setup=test.get("setup", {}),
                        call=test.get("call", {}),
                        teardown=test.get("teardown", {}),
                    )
                )
        if failed_tests:
            result_logger.warning(f"Found {len(failed_tests)} test failures")

    # Extract summary
    summary = PytestSummary(
        total=data.get("summary", {}).get("total", 0),
        failed=data.get("summary", {}).get("failed", 0),
        passed=data.get("summary", {}).get("passed", 0),
        skipped=data.get("summary", {}).get("skipped", 0),
        errors=data.get("summary", {}).get("errors", 0),
        xfailed=data.get("summary", {}).get("xfailed", 0),
        xpassed=data.get("summary", {}).get("xpassed", 0),
        collected=data.get("summary", {}).get("collected", 0),
        collection_failures=len(failed_collections),
    )
    result_logger.info(f"Test summary: {summary.model_dump()}")

    # Create the results object
    return PytestResults(
        summary=summary,
        failed_collections=failed_collections,
        failed_tests=failed_tests,
    )


def get_next_collection_error(processed_results, tool_function):
    """
    Get the next collection error to fix.

    Args:
        processed_results: The processed pytest results
        tool_function: The function to reference in the NextAction

    Returns:
        ToolResult: Error result with details about the collection error
    """
    # Return the first collection error to fix
    error = processed_results.failed_collections[0]
    result_logger.warning(f"Collection error found: {error.model_dump()}")

    next_action = NextAction(
        tool=tool_function,
        instructions=(
            "Fix the following error before you call the next mcp tool."
            "<error>\n"
            f"{error.model_dump()}\n"
            "</error>\n"
        ),
    )

    return ToolResult(
        status=ToolStatus.FAILURE,
        message=(
            "Collection error found. This is typically an import error or "
            "missing module. Please fix the error and try again."
        ),
        next_action=next_action,
    )


def get_next_test_failure(processed_results):
    """
    Get the next test failure to fix.

    Args:
        processed_results: The processed pytest results

    Returns:
        ToolResult: Error result with details about the test failure
    """
    failure = processed_results.failed_tests[0]
    result_logger.warning(f"Test failure found: {failure.model_dump()}")

    return ToolResult(
        status=ToolStatus.FAILURE,
        message=("Test failure found. Please fix the failing test and try again."),
    )
