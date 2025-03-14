"""Autoflake service functions for the pytest server."""

import json
from pathlib import Path
from typing import Any, Dict, Union

from mcp_suite.servers.qa import logger
from mcp_suite.servers.qa.config import ReportPaths


def process_flake8_results(
    input_file: Union[str, Path] = ReportPaths.AUTOFLAKE,
) -> Dict[str, Any]:
    """
    Process autoflake results JSON and extract issues.

    Args:
        input_file: Path to the autoflake results JSON file

    Returns:
        Dictionary containing summary and issues
    """
    logger.info(f"Processing flake8 results from {input_file}")

    # Convert string paths to Path objects if needed
    input_path = Path(input_file) if isinstance(input_file, str) else input_file
    logger.debug(f"Input path: {input_path}")

    try:
        # Check if the file exists
        if not input_path.exists():
            logger.warning(f"Flake8 results file not found: {input_path}")
            return {
                "Status": "Success",
                "Message": "No issues found (results file not present).",
                "Instructions": (
                    "Your code appears to be clean with no unused imports or variables."
                ),
            }

        # Load the JSON file
        logger.debug(f"Loading JSON from {input_path}")
        with open(input_path, "r") as f:
            results_data = json.load(f)

        # Flatten the results - extract all issues from files with non-empty arrays
        all_issues = []
        for _, issues in results_data.items():
            if issues:  # Only process non-empty lists
                all_issues.extend(issues)

        # If no issues found, return success
        if not all_issues:
            logger.info("No flake8 issues found")
            return {
                "Status": "Success",
                "Message": (
                    "Great job! Your code is clean with no unused imports or variables."
                ),
                "Instructions": (
                    "Your code is looking great! You are done! Great job! "
                    "Thank you so much."
                ),
            }

        # Get the first issue to fix
        first_issue = all_issues[0]
        logger.info(f"Found flake8 issue: {json.dumps(first_issue, indent=2)}")

        return {
            "Status": "Issues Found",
            "Issue": first_issue,
            "Instructions": (
                "Let's fix the issue in the file. After fixing this issue, run the "
                "mcp tool run_autoflake again to check for more issues."
            ),
        }

    except json.JSONDecodeError as e:
        error_msg = f"Error: Invalid JSON in {input_path}: {str(e)}"
        logger.error(error_msg)
        return {
            "Status": "Error",
            "Message": error_msg,
            "Instructions": (
                "There was an error processing the autoflake results. "
                "Please check if the file is valid JSON."
            ),
        }

    except Exception as e:
        error_msg = f"Error processing flake8 results: {str(e)}"
        logger.exception(error_msg)
        return {
            "Status": "Error",
            "Message": error_msg,
            "Instructions": (
                "There was an unexpected error processing the autoflake results. "
                "Please try running the tool again."
            ),
        }
