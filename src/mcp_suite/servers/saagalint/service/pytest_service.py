"""Pytest service functions for the pytest server."""

import json
from pathlib import Path
from typing import Union

# Replace direct loguru import with import from dev package
from src.mcp_suite.servers.saagalint import logger
from src.mcp_suite.servers.saagalint.config import ReportPaths
from src.mcp_suite.servers.saagalint.models.pytest_models import (
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

    try:
        # Load the JSON file
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
            for collector in results_data["collectors"]:
                if collector.get("outcome") == "failed":
                    failed_collections.append(PytestCollectionFailure(**collector))

        # Extract failed tests
        failed_tests = []
        for test in results_data["tests"]:
            if test.get("outcome") == "failed":
                # Create a copy of the test data without the keywords field
                test_copy = test.copy()
                if "keywords" in test_copy:
                    test_copy.pop("keywords")  # Remove the keywords field
                failed_tests.append(PytestFailedTest(**test_copy))

        # Create the summary
        summary_data = results_data.get("summary", {})
        summary = PytestSummary(
            total=summary_data.get("total", 0),
            failed=summary_data.get("failed", 0),
            passed=summary_data.get("passed", 0),
            skipped=summary_data.get("skipped", 0),
            errors=summary_data.get("errors", 0),
            xfailed=summary_data.get("xfailed", 0),
            xpassed=summary_data.get("xpassed", 0),
            collected=summary_data.get("collected", 0),
            collection_failures=len(failed_collections),
        )

        # Create the result object
        result = PytestResults(
            summary=summary,
            failed_collections=failed_collections,
            failed_tests=failed_tests,
        )

        # Write to the output file
        with open(output_path, "w") as f:
            f.write(result.model_dump_json(indent=2))

        logger.info(
            f"Processed pytest results: {result.summary.total} total, "
            f"{result.summary.failed} failed, "
            f"{result.summary.passed} passed"
        )
        return result

    except FileNotFoundError:
        error_msg = f"Error: Input file not found: {input_path}"
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
