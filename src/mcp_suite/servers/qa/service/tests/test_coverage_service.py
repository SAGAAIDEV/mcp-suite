"""Tests for the coverage service module."""

import json
from unittest.mock import mock_open, patch

import pytest

from mcp_suite.servers.qa.service.coverage import (
    CoverageIssue,
    _process_section,
    process_coverage_json,
    process_file_data,
)

# Remove logging test and fixture
# @pytest.fixture
# def capture_logs():
#     """Fixture to capture and test logging calls."""
#     mock_logger = MagicMock()
#     with patch("mcp_suite.servers.qa.service.coverage.logger", mock_logger):
#         yield mock_logger


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
        """Test processing coverage JSON with a specific file filter."""
        # Create a mock coverage data
        mock_data = {
            "files": {
                "src/mcp_suite/example1.py": {
                    "missing_lines": [10, 20],
                    "sections": {},
                    "functions": {},
                    "classes": {},
                },
                "src/mcp_suite/example2.py": {
                    "missing_lines": [30, 40],
                    "sections": {},
                    "functions": {},
                    "classes": {},
                },
            }
        }

        # Mock open to return our mock data
        mock_open_obj = mock_open(read_data=json.dumps(mock_data))

        with (
            patch("builtins.open", mock_open_obj),
            patch(
                "mcp_suite.servers.qa.service.coverage.process_file_data"
            ) as mock_process,
        ):
            # Call the function with a specific file
            _ = process_coverage_json(
                coverage_file="./reports/coverage.json", specific_file="example1"
            )

            # Verify process_file_data was called only for the matching file
            assert mock_process.call_count == 1
            # Check the file path passed to process_file_data
            args, _ = mock_process.call_args
            assert "example1" in args[0]

    def test_process_coverage_json_with_no_matching_files(self):
        """Test processing coverage JSON with no matching files."""
        # Create a mock coverage data
        mock_data = {
            "files": {
                "src/mcp_suite/example1.py": {
                    "missing_lines": [10, 20],
                    "sections": {},
                    "functions": {},
                    "classes": {},
                }
            }
        }

        # Mock open to return our mock data
        mock_open_obj = mock_open(read_data=json.dumps(mock_data))

        with patch("builtins.open", mock_open_obj):
            # Call the function with a non-matching file
            result = process_coverage_json(
                coverage_file="./reports/coverage.json", specific_file="nonexistent"
            )

            # Verify an empty list is returned
            assert result == []

    def test_process_coverage_json_with_invalid_data_structure(self):
        """Test processing coverage JSON with invalid data structure."""
        # Test with non-dictionary data
        mock_data_non_dict = "not a dictionary"
        mock_open_obj = mock_open(read_data=json.dumps(mock_data_non_dict))

        with patch("builtins.open", mock_open_obj):
            result = process_coverage_json()
            assert result == []

        # Test with missing 'files' key
        mock_data_no_files = {"not_files": {}}
        mock_open_obj = mock_open(read_data=json.dumps(mock_data_no_files))

        with patch("builtins.open", mock_open_obj):
            result = process_coverage_json()
            assert result == []

    def test_process_coverage_json_with_file_not_found(self):
        """Test processing coverage JSON with file not found error."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                process_coverage_json()

    def test_process_coverage_json_with_invalid_json(self):
        """Test processing coverage JSON with invalid JSON."""
        mock_open_obj = mock_open(read_data="invalid json")

        with patch("builtins.open", mock_open_obj):
            with pytest.raises(json.JSONDecodeError):
                process_coverage_json()

    def test_process_coverage_json_with_exception_in_processing(self):
        """Test processing coverage JSON with exception in processing."""
        # Create a mock coverage data
        mock_data = {
            "files": {
                "src/mcp_suite/example.py": {
                    "missing_lines": [10, 20],
                    "sections": {},
                    "functions": {},
                    "classes": {},
                }
            }
        }

        # Mock open to return our mock data
        mock_open_obj = mock_open(read_data=json.dumps(mock_data))

        with (
            patch("builtins.open", mock_open_obj),
            patch(
                "mcp_suite.servers.qa.service.coverage.process_file_data",
                side_effect=Exception("Test exception"),
            ),
        ):
            # Call the function
            result = process_coverage_json()

            # Verify an empty list is returned
            assert result == []

    def test_process_coverage_json_with_non_dict_file_data(self):
        """Test processing coverage JSON with non-dictionary file data."""
        # Create a mock coverage data with non-dictionary file data
        mock_data = {"files": {"src/mcp_suite/example.py": "not a dictionary"}}

        # Mock open to return our mock data
        mock_open_obj = mock_open(read_data=json.dumps(mock_data))

        with patch("builtins.open", mock_open_obj):
            # Call the function
            result = process_coverage_json()

            # Verify an empty list is returned since the file data is skipped
            assert result == []

    def test_process_coverage_json_with_specific_file_no_matches(self):
        """Test processing coverage JSON data with a specific file filter.

        Tests the case where no files match the filter.
        """
        # Create a sample with files that don't match the filter
        sample_data = {
            "files": {
                "src/mcp_suite/example.py": {
                    "missing_lines": [10, 20],
                    "functions": {
                        "example_function": {
                            "missing_lines": [15, 25],
                        }
                    },
                    "classes": {},
                },
            }
        }

        mock_json = json.dumps(sample_data)

        with patch("builtins.open", mock_open(read_data=mock_json)):
            issues = process_coverage_json(
                "fake_path.json", specific_file="nonexistent_file.py"
            )

        # We should have 0 issues since the file doesn't match the filter
        assert len(issues) == 0

    def test_process_coverage_json_with_specific_file_exception(self):
        """Test processing coverage JSON data with a specific file filter.

        Tests the case where processing raises an exception.
        """
        # Create a sample with files that match the filter
        sample_data = {
            "files": {
                "src/mcp_suite/example.py": {
                    "missing_lines": [10, 20],
                    "functions": {
                        "example_function": {
                            "missing_lines": [15, 25],
                        }
                    },
                    "classes": {},
                },
            }
        }

        mock_json = json.dumps(sample_data)

        # Mock process_file_data to raise an exception
        # only when called with specific_file
        original_process_file_data = process_file_data

        def mock_process_file_data(file_path, file_data, result):
            if "example.py" in file_path:
                raise Exception("Test exception")
            return original_process_file_data(file_path, file_data, result)

        with patch("builtins.open", mock_open(read_data=mock_json)):
            with patch(
                "mcp_suite.servers.qa.service.coverage.process_file_data",
                side_effect=mock_process_file_data,
            ):
                issues = process_coverage_json(
                    "fake_path.json", specific_file="example.py"
                )

        # We should have 0 issues since an exception was raised during processing
        assert issues == []

    def test_process_file_data(self):
        """Test processing file data with various combinations of data."""
        # Create a sample file data with functions and classes
        file_data = {
            "missing_lines": [10, 20],
            "functions": {
                "example_function": {
                    "missing_lines": [15, 25],
                    "missing_branches": [[1, 2], [3, 4]],
                },
                "another_function": {
                    "missing_lines": [],
                    "missing_branches": [],
                },
                "non_dict_function": "This is not a dictionary",
            },
            "classes": {
                "ExampleClass": {
                    "missing_lines": [35, 45],
                    "missing_branches": [[5, 6]],
                },
                "AnotherClass": {
                    "missing_lines": [],
                    "missing_branches": [],
                },
                "non_dict_class": "This is not a dictionary",
            },
        }

        result = []
        process_file_data("src/mcp_suite/example.py", file_data, result)

        # We should have issues for:
        # 1. example_function missing lines
        # 2. example_function missing branches
        # 3. ExampleClass missing lines
        # 4. ExampleClass missing branches
        assert len(result) == 4

        # Verify function issues
        function_issues = [i for i in result if i.section_name == "example_function"]
        assert len(function_issues) == 2

        # Verify class issues
        class_issues = [i for i in result if i.section_name == "ExampleClass"]
        assert len(class_issues) == 2

        # Test with 100% coverage file data
        file_data_100_percent = {
            "missing_lines": [],
            "missing_branches": [],
            "functions": {},
            "classes": {},
        }

        result = []
        process_file_data("src/mcp_suite/example.py", file_data_100_percent, result)

        # We should have no issues for a file with 100% coverage
        assert len(result) == 0

        # Test with no sections, functions, or classes
        file_data_basic = {
            "missing_lines": [10, 20],
            "missing_branches": {"1": [2, 3]},
        }

        result = []
        process_file_data("src/mcp_suite/example.py", file_data_basic, result)

        # We should have one issue for the basic file
        assert len(result) == 1
        assert result[0].file_path == "src/mcp_suite/example.py"
        assert result[0].section_name == ""
        assert result[0].missing_lines == [10, 20]
        assert len(result[0].missing_branches) == 1

    def test_process_file_data_exception(self):
        """Test processing file data that raises an exception."""
        # Create a sample file data
        file_data = {
            "missing_lines": [10, 20],
            "functions": {
                "example_function": {
                    "missing_lines": [15, 25],
                },
            },
            "classes": {},
            "sections": {
                "test_section": {
                    "missing_lines": [30, 40],
                },
            },
        }

        # Mock _process_section to raise an exception
        with patch(
            "mcp_suite.servers.qa.service.coverage._process_section",
            side_effect=Exception("Test exception"),
        ):
            result = []
            # This should raise an exception that will be caught by the try/except
            # in process_file_data
            with pytest.raises(Exception):
                process_file_data("src/mcp_suite/example.py", file_data, result)

        # Test with a file that has 100% coverage (should skip processing)
        file_data_100_percent = {
            "missing_lines": [],
            "missing_branches": [],
        }

        result = []
        process_file_data("src/mcp_suite/example.py", file_data_100_percent, result)

        # We should have no issues for a file with 100% coverage
        assert len(result) == 0

    def test_process_file_data_non_dict_entries(self):
        """Test processing file data with non-dictionary entries."""
        # Create a sample file data with non-dictionary entries
        file_data = {
            "missing_lines": [10, 20],
            "functions": {
                "non_dict_function": "This is not a dictionary",
            },
            "classes": {
                "non_dict_class": "This is not a dictionary",
            },
            "sections": None,  # Add this to ensure we don't have sections
        }

        result = []
        process_file_data("src/mcp_suite/example.py", file_data, result)

        # We should have one issue for the file-level missing lines
        assert len(result) == 1
        assert result[0].file_path == "src/mcp_suite/example.py"
        assert result[0].section_name == ""
        assert result[0].missing_lines == [10, 20]

    def test_process_file_data_with_empty_sections(self):
        """Test processing file data with empty sections."""
        # Create a sample file data with empty sections
        file_data = {
            "missing_lines": [10, 20],
            "sections": {},
            "functions": {},
            "classes": {},
        }

        result = []
        process_file_data("src/mcp_suite/example.py", file_data, result)

        # We should have one issue for the file-level missing lines
        assert len(result) == 1
        assert result[0].file_path == "src/mcp_suite/example.py"
        assert result[0].section_name == ""
        assert result[0].missing_lines == [10, 20]

    def test_process_file_data_with_sections(self):
        """Test processing file data with sections."""
        # Create a sample file data with sections
        file_data = {
            "missing_lines": [10, 20],
            "sections": {
                "test_section": {
                    "missing_lines": [30, 40],
                    "missing_branches": [[1, 2], [3, 4]],
                }
            },
            "functions": {},
            "classes": {},
        }

        # Mock _process_section to return a list of issues
        with patch(
            "mcp_suite.servers.qa.service.coverage._process_section"
        ) as mock_process_section:
            # Create a mock issue
            mock_issue = CoverageIssue(
                file_path="src/mcp_suite/example.py",
                section_name="test_section",
                missing_lines=[30, 40],
                missing_branches=None,
            )
            mock_process_section.return_value = [mock_issue]

            result = []
            process_file_data("src/mcp_suite/example.py", file_data, result)

            # We should have one issue from the section
            assert len(result) == 1
            assert result[0].file_path == "src/mcp_suite/example.py"
            assert result[0].section_name == "test_section"
            assert result[0].missing_lines == [30, 40]

    def test_process_coverage_json_with_general_exception(self):
        """Test processing coverage JSON with a general exception."""
        # Mock open to raise a general exception
        with patch("builtins.open", side_effect=Exception("General error")):
            # Call the function
            result = process_coverage_json()

            # Verify an empty list is returned
            assert result == []

    def test_process_section_with_missing_lines_and_branches(self):
        """Test processing a section with both missing lines and branches."""
        file_path = "src/mcp_suite/example.py"
        sections = {
            "test_section": {
                "missing_lines": [10, 20],
                "missing_branches": [[1, 2], [3, 4]],
            }
        }

        result = _process_section(file_path, sections)

        # We should have two issues: one for missing lines and one for missing branches
        assert len(result) == 2

        # Find the issue for missing lines
        lines_issue = next(i for i in result if i.missing_lines is not None)
        assert lines_issue.file_path == file_path
        assert lines_issue.section_name == "test_section"
        assert lines_issue.missing_lines == [10, 20]

        # Find the issue for missing branches
        branches_issue = next(i for i in result if i.missing_branches is not None)
        assert branches_issue.file_path == file_path
        assert branches_issue.section_name == "test_section"
        assert len(branches_issue.missing_branches) == 2
        assert branches_issue.missing_branches[0].source == 1
        assert branches_issue.missing_branches[0].target == 2

    def test_process_section_with_no_issues(self):
        """Test processing a section with no missing lines or branches."""
        file_path = "src/mcp_suite/example.py"
        sections = {
            "test_section": {
                "missing_lines": [],
                "missing_branches": [],
            }
        }

        result = _process_section(file_path, sections)

        # We should have no issues
        assert len(result) == 0

    def test_process_section_with_only_missing_lines(self):
        """Test processing a section with only missing lines."""
        file_path = "src/mcp_suite/example.py"
        sections = {
            "test_section": {
                "missing_lines": [10, 20],
            }
        }

        result = _process_section(file_path, sections)

        # We should have one issue for missing lines
        assert len(result) == 1
        assert result[0].file_path == file_path
        assert result[0].section_name == "test_section"
        assert result[0].missing_lines == [10, 20]
        assert result[0].missing_branches is None

    def test_process_section_with_only_missing_branches(self):
        """Test processing a section with only missing branches."""
        file_path = "src/mcp_suite/example.py"
        sections = {
            "test_section": {
                "missing_branches": [[1, 2], [3, 4]],
            }
        }

        result = _process_section(file_path, sections)

        # We should have one issue for missing branches
        assert len(result) == 1
        assert result[0].file_path == file_path
        assert result[0].section_name == "test_section"
        assert result[0].missing_lines is None
        assert len(result[0].missing_branches) == 2
        assert result[0].missing_branches[0].source == 1
        assert result[0].missing_branches[0].target == 2
