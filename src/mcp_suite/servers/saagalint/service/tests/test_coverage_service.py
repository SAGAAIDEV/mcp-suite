"""Tests for the coverage service module."""

import json
from unittest.mock import mock_open, patch

import pytest

# Import the centralized logger
from mcp_suite.servers.saagalint import logger

# Use absolute imports
from mcp_suite.servers.saagalint.service.coverage_service import (
    _process_section,
    process_coverage_json,
)

# Log test start
logger.info("Test coverage service module tests starting.")


# Instead of mocking the logger completely, let's create a test that verifies logging
# This will help ensure logs are being written
@pytest.fixture
def capture_logs():
    """Capture logs during a test."""
    with patch(
        "mcp_suite.servers.saagalint.service.coverage_service.logger"
    ) as mock_logger:
        yield mock_logger


class TestCoverageService:
    """Test class for the coverage service module."""

    # Sample coverage data for testing
    SAMPLE_COVERAGE_DATA = {
        "files": {
            "src/mcp_suite/example.py": {
                "missing_lines": [10, 20, 30],
                "functions": {
                    "example_function": {
                        "missing_lines": [15, 25],
                        "missing_branches": [[1, 2], [3, 4]],
                    }
                },
                "classes": {
                    "ExampleClass": {
                        "missing_lines": [35, 45],
                        "missing_branches": [[5, 6]],
                    }
                },
            },
            "src/mcp_suite/another_example.py": {
                "missing_lines": [],
                "functions": {},
                "classes": {},
            },
        }
    }

    def test_process_coverage_json(self):
        """Test processing coverage JSON data."""
        mock_json = json.dumps(self.SAMPLE_COVERAGE_DATA)

        with patch("builtins.open", mock_open(read_data=mock_json)):
            issues = process_coverage_json("fake_path.json")

        # We should have 4 issues:
        # 1 for function missing lines, 1 for function missing branches,
        # 1 for class missing lines, 1 for class missing branches
        assert len(issues) == 4

        # Verify the issues are correctly parsed
        function_issues = [i for i in issues if i.section_name == "example_function"]
        class_issues = [i for i in issues if i.section_name == "ExampleClass"]

        assert len(function_issues) == 2
        assert len(class_issues) == 2

        # Check missing lines in function
        function_lines_issue = next(i for i in function_issues if i.missing_lines)
        assert function_lines_issue.missing_lines == [15, 25]

        # Check missing branches in function
        function_branches_issue = next(i for i in function_issues if i.missing_branches)
        assert len(function_branches_issue.missing_branches) == 2
        assert function_branches_issue.missing_branches[0].source == 1
        assert function_branches_issue.missing_branches[0].target == 2

        # Check missing lines in class
        class_lines_issue = next(i for i in class_issues if i.missing_lines)
        assert class_lines_issue.missing_lines == [35, 45]

        # Check missing branches in class
        class_branches_issue = next(i for i in class_issues if i.missing_branches)
        assert len(class_branches_issue.missing_branches) == 1
        assert class_branches_issue.missing_branches[0].source == 5
        assert class_branches_issue.missing_branches[0].target == 6

    def test_process_coverage_json_with_specific_file(self):
        """Test processing coverage JSON data with a specific file filter."""
        mock_json = json.dumps(self.SAMPLE_COVERAGE_DATA)

        with patch("builtins.open", mock_open(read_data=mock_json)):
            issues = process_coverage_json("fake_path.json", specific_file="example.py")

        # We should still have 4 issues since we're filtering for example.py
        assert len(issues) == 4

        # All issues should be for the example.py file
        for issue in issues:
            assert "example.py" in issue.file_path

    def test_process_coverage_json_with_nonexistent_file(self):
        """Test processing coverage JSON data with a nonexistent file filter."""
        mock_json = json.dumps(self.SAMPLE_COVERAGE_DATA)

        with patch("builtins.open", mock_open(read_data=mock_json)):
            issues = process_coverage_json(
                "fake_path.json", specific_file="nonexistent.py"
            )

        # We should have 0 issues since the file doesn't exist in the coverage data
        assert len(issues) == 0

    def test_process_coverage_json_file_not_found(self):
        """Test handling file not found error."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                process_coverage_json("nonexistent_file.json")

    def test_process_coverage_json_invalid_json(self):
        """Test handling invalid JSON data."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with pytest.raises(json.JSONDecodeError):
                process_coverage_json("fake_path.json")

    def test_process_coverage_json_missing_files_key(self):
        """Test handling coverage data without 'files' key."""
        mock_json = json.dumps({"not_files": {}})

        with patch("builtins.open", mock_open(read_data=mock_json)):
            # Instead of expecting a KeyError, we now expect an empty list
            issues = process_coverage_json("fake_path.json")
            assert issues == []
            assert len(issues) == 0

    def test_process_coverage_json_not_a_dict(self):
        """Test handling coverage data that is not a dictionary."""
        mock_json = json.dumps([1, 2, 3])  # Array instead of dict

        with patch("builtins.open", mock_open(read_data=mock_json)):
            issues = process_coverage_json("fake_path.json")
            assert issues == []
            assert len(issues) == 0

    def test_process_coverage_json_with_non_dict_file_data(self):
        """Test handling coverage data with non-dictionary file data."""
        # Create a sample with a non-dictionary entry in files
        sample_data = {
            "files": {
                "src/mcp_suite/example.py": {
                    "missing_lines": [10, 20],  # Add missing lines at the file level
                    "functions": {
                        "example_function": {
                            "missing_lines": [15, 25],
                        }
                    },
                    "classes": {},  # Add this to ensure we have classes to process
                },
                "meta": "This is not a dict",  # This should be skipped
                "src/mcp_suite/no_issues.py": {
                    "missing_lines": [],
                    "missing_branches": [],
                    "functions": {},
                    "classes": {},
                },
            }
        }

        mock_json = json.dumps(sample_data)

        with patch("builtins.open", mock_open(read_data=mock_json)):
            issues = process_coverage_json("fake_path.json")

        # We should only have issues from example.py, not from meta or no_issues.py
        # Since example_function only has missing_lines, we should have 1 issue
        assert len(issues) == 1
        assert issues[0].file_path == "src/mcp_suite/example.py"
        assert issues[0].section_name == "example_function"
        assert issues[0].missing_lines == [15, 25]

    def test_process_coverage_json_with_no_issues_file(self):
        """Test handling coverage data with a file that has no issues."""
        # Create a sample with a file that has no missing lines or branches
        sample_data = {
            "files": {
                "src/mcp_suite/no_issues.py": {
                    "missing_lines": [],
                    "missing_branches": [],
                    "functions": {
                        "function_with_no_issues": {
                            "missing_lines": [],
                            "missing_branches": [],
                        }
                    },
                    "classes": {},
                }
            }
        }

        mock_json = json.dumps(sample_data)

        with patch("builtins.open", mock_open(read_data=mock_json)):
            issues = process_coverage_json("fake_path.json")

        # We should have no issues since the file has no missing lines or branches
        assert len(issues) == 0

    def test_process_coverage_json_generic_exception(self):
        """Test handling a generic exception during processing."""
        mock_json = json.dumps(self.SAMPLE_COVERAGE_DATA)

        # Simulate a generic exception during processing
        with patch("builtins.open", mock_open(read_data=mock_json)):
            with patch(
                "mcp_suite.servers.saagalint.service.coverage_service._process_section",
                side_effect=Exception("Generic error"),
            ):
                issues = process_coverage_json("fake_path.json")

        # The function returns an empty list when _process_section raises an exception
        # Exception is caught and logged, then an empty list is returned
        assert issues == []

    def test_process_coverage_json_top_level_exception(self):
        """Test handling a top-level exception during processing."""
        # Simulate a generic exception at the top level of the function
        with patch("builtins.open", side_effect=Exception("Top level error")):
            issues = process_coverage_json("fake_path.json")

        # We should get an empty list when a top-level exception occurs
        assert issues == []

    def test_process_section(self):
        """Test processing a section of coverage data."""
        file_path = "src/mcp_suite/example.py"
        sections = {
            "test_function": {
                "missing_lines": [10, 20],
                "missing_branches": [[1, 2], [3, 4]],
            },
            "another_function": {"missing_lines": [30, 40]},
        }

        issues = _process_section(file_path, sections)

        # We should have 3 issues (2 functions, one with both lines and branches)
        assert len(issues) == 3

        # Verify the issues are correctly parsed
        test_function_issues = [i for i in issues if i.section_name == "test_function"]
        another_function_issues = [
            i for i in issues if i.section_name == "another_function"
        ]

        assert len(test_function_issues) == 2
        assert len(another_function_issues) == 1

        # Check missing lines
        lines_issue = next(i for i in test_function_issues if i.missing_lines)
        assert lines_issue.missing_lines == [10, 20]

        # Check missing branches
        branches_issue = next(i for i in test_function_issues if i.missing_branches)
        assert len(branches_issue.missing_branches) == 2
        assert branches_issue.missing_branches[0].source == 1
        assert branches_issue.missing_branches[0].target == 2

    def test_process_section_empty(self):
        """Test processing an empty section."""
        file_path = "src/mcp_suite/example.py"
        sections = {}

        issues = _process_section(file_path, sections)

        # We should have 0 issues for an empty section
        assert len(issues) == 0

    def test_process_section_no_issues(self):
        """Test processing a section with no issues."""
        file_path = "src/mcp_suite/example.py"
        sections = {
            "test_function": {"no_missing_lines": [], "no_missing_branches": []}
        }

        issues = _process_section(file_path, sections)

        # We should have 0 issues since there are no missing lines or branches
        assert len(issues) == 0

    def test_logging(self, capture_logs):
        """Test that logging is working properly."""
        mock_json = json.dumps(self.SAMPLE_COVERAGE_DATA)

        with patch("builtins.open", mock_open(read_data=mock_json)):
            process_coverage_json("fake_path.json")

        # Verify that logging calls were made
        assert capture_logs.info.called
        assert capture_logs.info.call_count >= 2  # At least 2 info logs should be made
