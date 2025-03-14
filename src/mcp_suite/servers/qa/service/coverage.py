"""Coverage service functions for the pytest server."""

import json
from typing import Any, Dict, List

# Import logger directly from loguru
from mcp_suite.servers.qa.models.coverage_models import (
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
    try:
        with open(coverage_file, "r") as f:
            data = json.load(f)

        # Check if the data has the expected structure
        if not isinstance(data, dict):
            return []

        if "files" not in data:
            return []

        coverage_data = data["files"]
        result = []

        # Filter for specific file if provided
        if specific_file:
            coverage_data = {
                k: v
                for k, v in coverage_data.items()
                if k == specific_file or k.endswith(f"/{specific_file}")
            }
            if not coverage_data:
                return []

        # Iterate through each file in the coverage data
        for file_path, file_data in coverage_data.items():
            # Skip non-dict entries like "meta" or other special keys
            if not isinstance(file_data, dict):
                continue

            # Check if file has issues at the file level
            file_has_issues = bool(
                file_data.get("missing_branches", []) or file_data.get("missing_lines")
            )

            # Check if any function or class has issues (including empty string keys)
            section_has_issues = False
            for section_type in ["functions", "classes"]:
                sections = file_data.get(section_type, {})
                for _, section_data in sections.items():
                    if section_data.get("missing_branches", []) or section_data.get(
                        "missing_lines"
                    ):
                        section_has_issues = True
                        break
                if section_has_issues:
                    break

            # Skip files with no issues at any level
            if not (file_has_issues or section_has_issues):
                continue

            # Process sections with issues (functions and classes)
            for section_type in ["functions", "classes"]:
                result.extend(
                    _process_section(file_path, file_data.get(section_type, {}))
                )

        return result
    except FileNotFoundError:
        raise
    except json.JSONDecodeError:
        raise
    except Exception:
        # Return an empty list for any other errors to make the function more robust
        return []


def _process_section(file_path: str, sections: Dict[str, Any]) -> List[CoverageIssue]:
    """
    Process a section (functions or classes) and extract coverage issues.

    Args:
        file_path: Path to the file
        sections: Dictionary of sections (functions or classes)

    Returns:
        List of CoverageIssue objects
    """
    result = []

    for section_name, section_data in sections.items():
        # Process missing branches
        if missing_branches := section_data.get("missing_branches", []):
            # Convert branch data to BranchCoverage objects
            branch_objects = [
                (
                    BranchCoverage.from_list(branch)
                    if isinstance(branch, list)
                    else branch
                )
                for branch in missing_branches
            ]

            result.append(
                CoverageIssue(
                    file_path=file_path,
                    section_name=section_name,
                    missing_branches=branch_objects,
                )
            )

        # Process missing lines
        if missing_lines := section_data.get("missing_lines", []):
            result.append(
                CoverageIssue(
                    file_path=file_path,
                    section_name=section_name,
                    missing_lines=missing_lines,
                )
            )

    return result


if __name__ == "__main__":  # pragma: no cover
    # Example usage
    issues = process_coverage_json()
    for issue in issues:
        print(issue)
