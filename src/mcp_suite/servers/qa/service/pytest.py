"""Pytest service functions for the pytest server."""

import json
from pathlib import Path
from typing import Union

from mcp_suite.servers.qa import logger
from mcp_suite.servers.qa.config import ReportPaths
from mcp_suite.servers.qa.models.pytest_models import (
    PytestCollectionFailure,
    PytestFailedTest,
    PytestResults,
    PytestSummary,
)


def process_pytest_results(
    input_file: Union[str, Path] = ReportPaths.PYTEST_RESULTS.value,
    output_file: Union[str, Path] = ReportPaths.FAILED_TESTS.value,
) -> PytestResults:
    """
    Process pytest results JSON and extract failed collections and failed tests.

    Args:
        input_file: Path to the pytest results JSON file
        output_file: Path to write the processed results

    Returns:
        PytestResults object containing summary, failed collections, and failed tests

    Raises:
        FileNotFoundError: If the input file doesn't exist
        json.JSONDecodeError: If the input file isn't valid JSON
        KeyError: If the input file doesn't have the expected structure
    """
    logger.info(f"Processing pytest results from {input_file}")

    # Convert string paths to Path objects if needed
    input_path = Path(input_file) if isinstance(input_file, str) else input_file
    output_path = Path(output_file) if isinstance(output_file, str) else output_file
    logger.debug(f"Input path: {input_path}, Output path: {output_path}")

    try:
        # Load the JSON file
        logger.debug(f"Loading JSON from {input_path}")
        with open(input_path, "r") as f:
            results_data = json.load(f)

        # Ensure tests key exists
        if "tests" not in results_data:
            error_msg = f"Error: 'tests' key not found in {input_path}"
            logger.error(error_msg)
            return PytestResults(summary=PytestSummary(), error=error_msg)

        # Extract failed collections
        failed_collections = []
        if "collectors" in results_data:
            logger.debug("Processing collection errors")
            # Handle both formats: list of collectors or dict with errors key
            if isinstance(results_data["collectors"], list):
                for collector in results_data["collectors"]:
                    if collector.get("outcome") == "failed":
                        failed_collections.append(
                            PytestCollectionFailure(
                                nodeid=collector.get("nodeid", "Unknown"),
                                outcome=collector.get("outcome", "failed"),
                                longrepr=collector.get("longrepr", "Unknown error"),
                            )
                        )
            elif (
                isinstance(results_data["collectors"], dict)
                and "errors" in results_data["collectors"]
            ):
                for error in results_data["collectors"]["errors"]:
                    failed_collections.append(
                        PytestCollectionFailure(
                            nodeid=error.get("nodeid", "Unknown"),
                            outcome="failed",
                            longrepr=error.get("longrepr", "Unknown error"),
                        )
                    )
            if failed_collections:
                logger.warning(f"Found {len(failed_collections)} collection errors")

        # Extract failed tests
        failed_tests = []
        if "tests" in results_data:
            logger.debug("Processing test failures")
            for test in results_data["tests"]:
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
                logger.warning(f"Found {len(failed_tests)} test failures")

        # Extract summary
        summary = PytestSummary(
            total=results_data.get("summary", {}).get("total", 0),
            failed=results_data.get("summary", {}).get("failed", 0),
            passed=results_data.get("summary", {}).get("passed", 0),
            skipped=results_data.get("summary", {}).get("skipped", 0),
            errors=results_data.get("summary", {}).get("errors", 0),
            xfailed=results_data.get("summary", {}).get("xfailed", 0),
            xpassed=results_data.get("summary", {}).get("xpassed", 0),
            collected=results_data.get("summary", {}).get("collected", 0),
            collection_failures=len(failed_collections),
        )
        logger.info(f"Test summary: {summary.model_dump()}")

        # Create the results object
        results = PytestResults(
            summary=summary,
            failed_collections=failed_collections,
            failed_tests=failed_tests,
        )

        # Write the results to the output file
        logger.debug(f"Writing results to {output_path}")
        with open(output_path, "w") as f:
            json.dump(results.model_dump(), f, indent=2)

        return results

    except FileNotFoundError:
        error_msg = f"Error: File not found: {input_path}"
        logger.error(error_msg)
        return PytestResults(summary=PytestSummary(), error=error_msg)

    except json.JSONDecodeError as e:
        error_msg = f"Error: Invalid JSON in {input_path}: {str(e)}"
        logger.error(error_msg)
        return PytestResults(summary=PytestSummary(), error=error_msg)

    except Exception as e:
        error_msg = f"Error processing pytest results: {str(e)}"
        logger.exception(error_msg)
        return PytestResults(summary=PytestSummary(), error=error_msg)


if __name__ == "__main__":  # pragma: no cover
    # Example usage
    results = process_pytest_results()
    print(f"Failed tests: {len(results.failed_tests)}")
    print(f"Failed collections: {len(results.failed_collections)}")
