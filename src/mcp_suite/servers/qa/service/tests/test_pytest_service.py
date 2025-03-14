"""Tests for the pytest_service module."""

import json
from unittest.mock import mock_open, patch

from mcp_suite.servers.qa.config import ReportPaths
from mcp_suite.servers.qa.models.pytest_models import (
    PytestResults,
)
from mcp_suite.servers.qa.service.pytest_service import (
    process_pytest_results,
)


class TestProcessPytestResults:
    """Tests for the process_pytest_results function."""

    def test_process_valid_results(self, tmp_path):
        """Test processing valid pytest results."""
        # Setup - create a mock pytest results file
        mock_results = {
            "tests": [
                {
                    "nodeid": "test_file.py::test_function",
                    "outcome": "passed",
                },
                {
                    "nodeid": "test_file.py::test_failing",
                    "outcome": "failed",
                    "keywords": {"test_failing": 1},
                    "longrepr": "AssertionError: expected 1 but got 2",
                    "duration": 0.01,
                },
            ],
            "collectors": [
                {
                    "nodeid": "test_file.py",
                    "outcome": "passed",
                }
            ],
            "summary": {
                "total": 2,
                "failed": 1,
                "passed": 1,
                "skipped": 0,
                "errors": 0,
                "xfailed": 0,
                "xpassed": 0,
                "collected": 2,
            },
        }

        # Create temporary input and output files
        input_file = tmp_path / "pytest_results.json"
        output_file = tmp_path / "failed_tests.json"

        with open(input_file, "w") as f:
            json.dump(mock_results, f)

        # Exercise - call the function
        result = process_pytest_results(input_file, output_file)

        # Verify - check that the result is as expected
        assert isinstance(result, PytestResults)
        assert result.summary.total == 2
        assert result.summary.failed == 1
        assert result.summary.passed == 1
        assert len(result.failed_tests) == 1
        assert result.failed_tests[0].nodeid == "test_file.py::test_failing"
        assert result.failed_tests[0].outcome == "failed"
        assert result.failed_tests[0].longrepr == "AssertionError: expected 1 but got 2"
        assert result.failed_tests[0].duration == 0.01
        assert "keywords" not in result.failed_tests[0].model_dump()
        assert len(result.failed_collections) == 0

        # Verify the output file was created
        assert output_file.exists()
        with open(output_file, "r") as f:
            output_data = json.loads(f.read())
            assert output_data["summary"]["total"] == 2
            assert output_data["summary"]["failed"] == 1
            assert len(output_data["failed_tests"]) == 1

    def test_process_with_collection_failures(self):
        """Test processing results with collection failures."""
        # Setup - create mock data with collection failures
        mock_results = {
            "tests": [],
            "collectors": [
                {
                    "nodeid": "test_file.py",
                    "outcome": "failed",
                    "longrepr": "ImportError: No module named 'missing_module'",
                }
            ],
            "summary": {
                "total": 0,
                "failed": 0,
                "passed": 0,
                "skipped": 0,
                "errors": 1,
                "xfailed": 0,
                "xpassed": 0,
                "collected": 0,
            },
        }

        # Mock the open function to return our mock data
        mock_file = mock_open(read_data=json.dumps(mock_results))

        with (
            patch("builtins.open", mock_file),
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Exercise - call the function
            result = process_pytest_results()

        # Verify - check that the result is as expected
        assert isinstance(result, PytestResults)
        assert result.summary.total == 0
        assert result.summary.errors == 1
        assert len(result.failed_collections) == 1
        assert result.failed_collections[0].nodeid == "test_file.py"
        assert result.failed_collections[0].outcome == "failed"
        assert (
            result.failed_collections[0].longrepr
            == "ImportError: No module named 'missing_module'"
        )
        assert len(result.failed_tests) == 0

    def test_missing_tests_key(self):
        """Test handling of missing 'tests' key in results."""
        # Setup - create mock data with missing 'tests' key
        mock_results = {
            "collectors": [],
            "summary": {
                "total": 0,
                "failed": 0,
                "passed": 0,
                "skipped": 0,
                "errors": 0,
                "xfailed": 0,
                "xpassed": 0,
                "collected": 0,
            },
        }

        # Mock the open function to return our mock data
        mock_file = mock_open(read_data=json.dumps(mock_results))

        with (
            patch("builtins.open", mock_file),
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Exercise - call the function
            result = process_pytest_results()

        # Verify - check that the result is as expected
        assert isinstance(result, PytestResults)
        assert (
            result.error
            == f"Error: 'tests' key not found in {ReportPaths.PYTEST_RESULTS.value}"
        )
        assert result.summary.total == 0
        assert len(result.failed_collections) == 0
        assert len(result.failed_tests) == 0

    def test_file_not_found(self):
        """Test handling of file not found error."""
        # Mock the open function to raise FileNotFoundError
        with (
            patch("builtins.open", side_effect=FileNotFoundError()),
            patch("pathlib.Path.exists", return_value=False),
        ):

            # Exercise - call the function
            result = process_pytest_results()

        # Verify - check that the result is as expected
        assert isinstance(result, PytestResults)
        assert "Error: Input file not found" in result.error
        assert result.summary.total == 0
        assert len(result.failed_collections) == 0
        assert len(result.failed_tests) == 0

    def test_invalid_json(self):
        """Test handling of invalid JSON in the input file."""
        # Mock the open function to return invalid JSON
        mock_file = mock_open(read_data="invalid json")

        with (
            patch("builtins.open", mock_file),
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Exercise - call the function
            result = process_pytest_results()

        # Verify - check that the result is as expected
        assert isinstance(result, PytestResults)
        assert "Error: Invalid JSON" in result.error
        assert result.summary.total == 0
        assert len(result.failed_collections) == 0
        assert len(result.failed_tests) == 0

    def test_general_exception(self):
        """Test handling of general exceptions."""
        # Mock the open function to raise a general exception
        with (
            patch("builtins.open", side_effect=Exception("Test exception")),
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Exercise - call the function
            result = process_pytest_results()

        # Verify - check that the result is as expected
        assert isinstance(result, PytestResults)
        assert "Error processing pytest results: Test exception" in result.error
        assert result.summary.total == 0
        assert len(result.failed_collections) == 0
        assert len(result.failed_tests) == 0

    def test_string_path_conversion(self, tmp_path):
        """Test conversion of string paths to Path objects."""
        # Setup - create a mock pytest results file
        mock_results = {
            "tests": [],
            "summary": {
                "total": 0,
                "failed": 0,
                "passed": 0,
                "skipped": 0,
                "errors": 0,
                "xfailed": 0,
                "xpassed": 0,
                "collected": 0,
            },
        }

        # Create temporary input and output files
        input_file = tmp_path / "pytest_results.json"
        output_file = tmp_path / "failed_tests.json"

        with open(input_file, "w") as f:
            json.dump(mock_results, f)

        # Exercise - call the function with string paths
        result = process_pytest_results(str(input_file), str(output_file))

        # Verify - check that the result is as expected
        assert isinstance(result, PytestResults)
        assert result.summary.total == 0
        assert len(result.failed_tests) == 0
        assert len(result.failed_collections) == 0

        # Verify the output file was created
        assert output_file.exists()

    def test_write_error(self, tmp_path):
        """Test handling of errors when writing the output file."""
        # Setup - create a mock pytest results file
        mock_results = {
            "tests": [],
            "summary": {
                "total": 0,
                "failed": 0,
                "passed": 0,
                "skipped": 0,
                "errors": 0,
                "xfailed": 0,
                "xpassed": 0,
                "collected": 0,
            },
        }

        # Create temporary input file
        input_file = tmp_path / "pytest_results.json"

        with open(input_file, "w") as f:
            json.dump(mock_results, f)

        # Mock the open function for writing to raise an exception
        original_open = open

        def mock_open_with_write_error(*args, **kwargs):
            if args[0] == input_file and "r" in kwargs.get("mode", "r"):
                return original_open(*args, **kwargs)
            else:
                raise PermissionError("Permission denied")

        with patch("builtins.open", side_effect=mock_open_with_write_error):
            # Exercise - call the function
            result = process_pytest_results(
                input_file, "/nonexistent/path/failed_tests.json"
            )

        # Verify - check that the result is as expected
        assert isinstance(result, PytestResults)
        assert result.summary.total == 0
        assert len(result.failed_tests) == 0
        assert len(result.failed_collections) == 0
        # The function should still return a result even if writing fails
