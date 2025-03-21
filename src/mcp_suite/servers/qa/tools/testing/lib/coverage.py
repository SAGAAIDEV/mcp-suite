"""Coverage service functions for the pytest server."""

import json
from typing import Any, Dict, List, Union

from mcp_suite.servers.qa.config import logger
from mcp_suite.servers.qa.tools.testing.models.coverage_models import (
    BranchCoverage,
    CoverageIssue,
)

# Remove redundant import and setup since it's already done in __init__.py
# from mcp_suite.servers.dev.config.config import setup_logging
# setup_logging("services")


def process_coverage_json(
    coverage_file: str = "./reports/coverage.json", specific_file: str = ""
) -> List[CoverageIssue]:
    """
    Process coverage JSON and extract only files with missing lines or branches.
    For problematic files, also examine functions and classes.

    Args:
        coverage_file: Path to the coverage JSON file
        specific_file: Optional file path to filter results for a specific file

    Returns:
        A list of CoverageIssue objects

    Raises:
        FileNotFoundError: If the coverage file doesn't exist
        json.JSONDecodeError: If the coverage file contains invalid JSON
    """
    logger.info(f"Processing coverage data from {coverage_file}")
    if specific_file:
        logger.info(f"Filtering for specific file: {specific_file}")

    try:
        logger.debug(f"Opening coverage file: {coverage_file}")
        with open(coverage_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check if the data has the expected structure
        if not isinstance(data, dict):
            logger.warning("Coverage data is not a dictionary")
            return []

        if "files" not in data:
            logger.warning("Coverage data does not contain 'files' key")
            return []

        coverage_data = data["files"]
        result = []

        # Filter for specific file if provided
        if specific_file:
            # Find the closest match if exact match not found
            matching_files = [
                path for path in coverage_data.keys() if specific_file in path
            ]

            if not matching_files:
                logger.warning(f"No matching files found for {specific_file}")
                return []

            logger.debug(
                f"Found {len(matching_files)} matching files: {matching_files}"
            )

            # Process each matching file
            for file_path in matching_files:
                file_data = coverage_data[file_path]
                try:
                    process_file_data(file_path, file_data, result)
                except Exception as e:
                    logger.exception(f"Error processing file {file_path}: {e}")
                    # If an exception occurs during processing, return an empty list
                    return []
        else:
            # Process all files with coverage issues
            for file_path, file_data in coverage_data.items():
                if not isinstance(file_data, dict):
                    logger.warning(f"Skipping {file_path} - data is not a dictionary")
                    continue

                try:
                    process_file_data(file_path, file_data, result)
                except Exception as e:
                    logger.exception(f"Error processing file {file_path}: {e}")
                    # If an exception occurs during processing, return an empty list
                    return []

        logger.info(f"Found {len(result)} coverage issues")
        return result

    except FileNotFoundError:
        logger.error(f"Coverage file not found: {coverage_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in coverage file: {e}")
        raise
    except (OSError, PermissionError, RuntimeError, IOError, ValueError) as e:
        logger.exception(f"Error processing coverage data: {e}")
        return []


def process_file_data(
    file_path: str, file_data: Dict[str, Any], result: List[CoverageIssue]
) -> None:
    """
    Process coverage data for a single file.

    Args:
        file_path: Path to the file
        file_data: Coverage data for the file
        result: List to append issues to
    """
    # Skip files with 100% coverage
    if ("missing_lines" not in file_data or not file_data["missing_lines"]) and (
        "missing_branches" not in file_data or not file_data["missing_branches"]
    ):
        logger.debug(f"Skipping {file_path} - has 100% coverage")
        return

    logger.debug(f"Processing file with coverage issues: {file_path}")

    try:
        has_processed_issues = False

        # Process sections if available
        if "sections" in file_data and file_data["sections"] is not None:
            section_issues = _process_section(file_path, file_data["sections"])
            if section_issues:
                result.extend(section_issues)
                has_processed_issues = True

        # Process functions if available
        if "functions" in file_data and file_data["functions"]:
            logger.debug(f"Processing functions for {file_path}")
            has_function_issues = False
            for func_name, func_data in file_data["functions"].items():
                if not isinstance(func_data, dict):
                    continue

                # Process missing lines
                if "missing_lines" in func_data and func_data["missing_lines"]:
                    issue = CoverageIssue(
                        file_path=file_path,
                        section_name=func_name,
                        missing_lines=func_data["missing_lines"],
                        missing_branches=None,
                    )
                    result.append(issue)
                    has_function_issues = True
                    has_processed_issues = True
                    logger.debug(f"Added issue for function {func_name} missing lines")

                # Process missing branches
                if "missing_branches" in func_data and func_data["missing_branches"]:
                    branches = []
                    for branch in func_data["missing_branches"]:
                        if isinstance(branch, list) and len(branch) == 2:
                            branches.append(
                                BranchCoverage(source=branch[0], target=branch[1])
                            )

                    if branches:
                        issue = CoverageIssue(
                            file_path=file_path,
                            section_name=func_name,
                            missing_lines=None,
                            missing_branches=branches,
                        )
                        result.append(issue)
                        has_function_issues = True
                        has_processed_issues = True
                        logger.debug(
                            f"Added issue for function {func_name} missing branches"
                        )

            if not has_function_issues:
                logger.debug(f"No function issues found for {file_path}")

        # Process classes if available
        if "classes" in file_data and file_data["classes"]:
            logger.debug(f"Processing classes for {file_path}")
            has_class_issues = False
            for class_name, class_data in file_data["classes"].items():
                if not isinstance(class_data, dict):
                    continue

                # Process missing lines
                if "missing_lines" in class_data and class_data["missing_lines"]:
                    issue = CoverageIssue(
                        file_path=file_path,
                        section_name=class_name,
                        missing_lines=class_data["missing_lines"],
                        missing_branches=None,
                    )
                    result.append(issue)
                    has_class_issues = True
                    has_processed_issues = True
                    logger.debug(f"Added issue for class {class_name} missing lines")

                # Process missing branches
                if "missing_branches" in class_data and class_data["missing_branches"]:
                    branches = []
                    for branch in class_data["missing_branches"]:
                        if isinstance(branch, list) and len(branch) == 2:
                            branches.append(
                                BranchCoverage(source=branch[0], target=branch[1])
                            )

                    if branches:
                        issue = CoverageIssue(
                            file_path=file_path,
                            section_name=class_name,
                            missing_lines=None,
                            missing_branches=branches,
                        )
                        result.append(issue)
                        has_class_issues = True
                        has_processed_issues = True
                        logger.debug(
                            f"Added issue for class {class_name} missing branches"
                        )

            if not has_class_issues:
                logger.debug(f"No class issues found for {file_path}")

        # If no issues were processed, create a basic issue for the file
        if not has_processed_issues:
            issue = CoverageIssue(
                file_path=file_path,
                section_name="",  # Empty section name for file-level issues
                missing_lines=file_data.get("missing_lines", []),
                missing_branches=_process_branches(
                    file_data.get("missing_branches", {})
                ),
            )
            result.append(issue)
            logger.debug(f"Added basic issue for {file_path}")
    except (
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
        IndexError,
        json.JSONDecodeError,
    ) as e:
        # If any exception occurs during processing, log it and re-raise
        # to be caught by the main function
        logger.exception(f"Error processing file {file_path}: {e}")
        raise


def _process_section(file_path: str, sections: Dict[str, Any]) -> List[CoverageIssue]:
    """
    Process sections of a file to extract coverage issues.

    Args:
        file_path: Path to the file
        sections: Dictionary of sections from coverage data

    Returns:
        List of CoverageIssue objects
    """
    logger.debug(f"Processing sections for {file_path}")
    result = []

    for section_name, section_data in sections.items():
        # Skip sections with 100% coverage
        if (
            "missing_lines" not in section_data or not section_data["missing_lines"]
        ) and (
            "missing_branches" not in section_data
            or not section_data["missing_branches"]
        ):
            continue

        # Create separate issues for missing lines and missing branches
        if "missing_lines" in section_data and section_data["missing_lines"]:
            # Create an issue for missing lines
            issue = CoverageIssue(
                file_path=file_path,
                section_name=section_name,
                missing_lines=section_data.get("missing_lines", []),
                missing_branches=None,
            )
            result.append(issue)
            logger.debug(
                f"Added issue for section {section_name} missing lines in {file_path}"
            )

        if "missing_branches" in section_data and section_data["missing_branches"]:
            # Create an issue for missing branches
            issue = CoverageIssue(
                file_path=file_path,
                section_name=section_name,
                missing_lines=None,
                missing_branches=_process_branches(
                    section_data.get("missing_branches", [])
                ),
            )
            result.append(issue)
            logger.debug(
                f"Added issue for section {section_name} missing branches in {file_path}"
            )

    return result


def _process_branches(
    branches_data: Union[Dict[str, List[int]], List[List[int]]],
) -> List[BranchCoverage]:
    """
    Process branch coverage data.

    Args:
        branches_data: Dictionary of branch coverage data or list of branch lists

    Returns:
        List of BranchCoverage objects
    """
    result = []

    # Handle dictionary format (from file-level missing_branches)
    if isinstance(branches_data, dict):
        for line_num, branches in branches_data.items():
            branch_cov = BranchCoverage(
                source=int(line_num),
                target=branches[0] if branches else 0,
            )
            result.append(branch_cov)
    # Handle list format (from function/class level missing_branches)
    elif isinstance(branches_data, list):
        for branch in branches_data:
            if isinstance(branch, list) and len(branch) == 2:
                branch_cov = BranchCoverage(
                    source=branch[0],
                    target=branch[1],
                )
                result.append(branch_cov)

    return result


if __name__ == "__main__":  # pragma: no cover
    # Example usage
    issues = process_coverage_json()
    for issue in issues:
        print(issue)
