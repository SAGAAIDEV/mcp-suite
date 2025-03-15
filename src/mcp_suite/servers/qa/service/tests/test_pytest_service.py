"""Tests for the pytest module."""

import json
from unittest.mock import mock_open, patch

import pytest

from mcp_suite.servers.qa.config import ReportPaths
from mcp_suite.servers.qa.models.pytest_models import (
    PytestResults,
)
from mcp_suite.servers.qa.service.pytest import (
    process_pytest_results,
    process_test_phase,
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
            # Exercise - call the function and expect a FileNotFoundError
            with pytest.raises(FileNotFoundError):
                process_pytest_results()

    def test_invalid_json(self):
        """Test handling of invalid JSON in the input file."""
        # Mock the open function to return invalid JSON
        mock_file = mock_open(read_data="invalid json")

        with (
            patch("builtins.open", mock_file),
            patch("pathlib.Path.exists", return_value=True),
        ):
            # Exercise - call the function and expect a JSONDecodeError
            with pytest.raises(json.JSONDecodeError):
                process_pytest_results()

    def test_general_exception(self):
        """Test handling of general exceptions."""
        # Mock the open function to raise a general exception
        with (
            patch("builtins.open", side_effect=Exception("Test exception")),
            patch("pathlib.Path.exists", return_value=True),
        ):
            # Exercise - call the function and expect an Exception
            with pytest.raises(Exception):
                process_pytest_results()

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
            # Exercise - call the function and expect a PermissionError
            with pytest.raises(PermissionError):
                process_pytest_results(
                    input_file, "/nonexistent/path/failed_tests.json"
                )

    def test_process_with_collectors_dict(self):
        """Test processing results with collectors as a dictionary."""
        # Setup - create mock data with collectors as a dictionary
        mock_results = {
            "tests": [],
            "collectors": {
                "errors": [
                    {
                        "nodeid": "test_file.py",
                        "longrepr": "ImportError: No module named 'missing_module'",
                    }
                ]
            },
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

    def test_process_with_call_information(self, tmp_path):
        """Test processing results with detailed call information."""
        # Setup - create mock data with call information
        mock_results = {
            "tests": [
                {
                    "nodeid": "test_file.py::test_failing",
                    "outcome": "failed",
                    "call": {
                        "duration": 0.0007015419996605488,
                        "outcome": "failed",
                        "crash": {
                            "path": "/path/to/test_file.py",
                            "lineno": 71,
                            "message": "AssertionError: assert 4 == 3",
                        },
                        "traceback": [
                            {
                                "path": "src/test_file.py",
                                "lineno": 71,
                                "message": "AssertionError",
                            }
                        ],
                        "longrepr": (
                            "self = <test_object>\n\n"
                            "    def test_function():\n"
                            "        assert 4 == 3\n"
                            "E       AssertionError: assert 4 == 3"
                        ),
                    },
                    "setup": {"duration": 0.001, "outcome": "passed"},
                    "teardown": {"duration": 0.0003, "outcome": "passed"},
                }
            ],
            "summary": {
                "total": 1,
                "failed": 1,
                "passed": 0,
                "skipped": 0,
                "errors": 0,
                "xfailed": 0,
                "xpassed": 0,
                "collected": 1,
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
        assert result.summary.total == 1
        assert result.summary.failed == 1
        assert len(result.failed_tests) == 1

        # Verify call information
        failed_test = result.failed_tests[0]
        assert failed_test.nodeid == "test_file.py::test_failing"
        assert failed_test.outcome == "failed"

        # Check call phase
        assert failed_test.call is not None
        assert failed_test.call.duration == 0.0007015419996605488
        assert failed_test.call.outcome == "failed"

        # Check crash info
        assert failed_test.call.crash is not None
        assert failed_test.call.crash.path == "/path/to/test_file.py"
        assert failed_test.call.crash.lineno == 71
        assert failed_test.call.crash.message == "AssertionError: assert 4 == 3"

        # Check traceback
        assert failed_test.call.traceback is not None
        assert len(failed_test.call.traceback) == 1
        assert failed_test.call.traceback[0].path == "src/test_file.py"
        assert failed_test.call.traceback[0].lineno == 71
        assert failed_test.call.traceback[0].message == "AssertionError"

        # Check longrepr
        assert "AssertionError: assert 4 == 3" in failed_test.call.longrepr

        # Check setup and teardown phases
        assert failed_test.setup is not None
        assert failed_test.setup.duration == 0.001
        assert failed_test.setup.outcome == "passed"

        assert failed_test.teardown is not None
        assert failed_test.teardown.duration == 0.0003
        assert failed_test.teardown.outcome == "passed"

    def test_process_test_phase_function(self):
        """Test the process_test_phase helper function."""
        # Test with None input
        assert process_test_phase(None) is None

        # Test with minimal input
        minimal_phase = {"outcome": "passed", "duration": 0.001}
        result = process_test_phase(minimal_phase)
        assert result is not None
        assert result.outcome == "passed"
        assert result.duration == 0.001
        assert result.crash is None
        assert result.traceback is None

        # Test with complete input
        complete_phase = {
            "duration": 0.002,
            "outcome": "failed",
            "crash": {
                "path": "/path/to/file.py",
                "lineno": 42,
                "message": "Error message",
            },
            "traceback": [{"path": "src/file.py", "lineno": 42, "message": "Error"}],
            "longrepr": "Detailed error message",
        }

        result = process_test_phase(complete_phase)
        assert result is not None
        assert result.outcome == "failed"
        assert result.duration == 0.002
        assert result.longrepr == "Detailed error message"

        # Check crash info
        assert result.crash is not None
        assert result.crash.path == "/path/to/file.py"
        assert result.crash.lineno == 42
        assert result.crash.message == "Error message"

        # Check traceback
        assert result.traceback is not None
        assert len(result.traceback) == 1
        assert result.traceback[0].path == "src/file.py"
        assert result.traceback[0].lineno == 42
        assert result.traceback[0].message == "Error"
