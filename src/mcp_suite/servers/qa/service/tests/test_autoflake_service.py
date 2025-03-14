"""Tests for the autoflake service."""

import json
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from mcp_suite.servers.qa.service.autoflake_service import (
    process_autoflake_results,
)


@pytest.fixture
def sample_autoflake_results():
    """Sample autoflake results for testing."""
    return {
        "src/module/example.py": [
            {
                "code": "F401",
                "filename": "src/module/example.py",
                "line_number": 3,
                "column_number": 1,
                "text": "'os' imported but unused",
                "physical_line": "import os",
            },
            {
                "code": "F841",
                "filename": "src/module/example.py",
                "line_number": 10,
                "column_number": 5,
                "text": "local variable 'unused_var' is assigned to but never used",
                "physical_line": "    unused_var = 'test'",
            },
        ],
    }


def test_process_autoflake_results_file_not_found():
    """Test processing autoflake results when the file doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Use a non-existent file
        non_existent_file = Path(temp_dir) / "non_existent.json"
        result = process_autoflake_results(non_existent_file)

        assert result["Status"] == "Success"
        assert "No issues found" in result["Message"]


def test_process_autoflake_results_empty_results():
    """Test processing autoflake results when there are no issues."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create an empty results file
        results_file = Path(temp_dir) / "empty_results.json"
        with open(results_file, "w") as f:
            json.dump({}, f)

        result = process_autoflake_results(results_file)

        assert result["Status"] == "Success"
        assert "Great job!" in result["Message"]


def test_process_autoflake_results_with_issues(sample_autoflake_results):
    """Test processing autoflake results when there are issues."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a results file with issues
        results_file = Path(temp_dir) / "results_with_issues.json"
        with open(results_file, "w") as f:
            json.dump(sample_autoflake_results, f)

        result = process_autoflake_results(results_file)

        assert result["Status"] == "Issues Found"
        assert "Issue" in result
        assert result["Issue"]["filename"] == "src/module/example.py"
        assert result["Issue"]["line_number"] == 3
        assert result["Issue"]["code"] == "F401"


def test_process_autoflake_results_invalid_json():
    """Test processing autoflake results when the JSON is invalid."""
    with patch("builtins.open", mock_open(read_data="invalid json")):
        with patch("pathlib.Path.exists", return_value=True):
            result = process_autoflake_results("fake_path.json")

            assert result["Status"] == "Error"
            assert "Invalid JSON" in result["Message"]


def test_process_autoflake_results_exception():
    """Test processing autoflake results when an exception occurs."""
    with patch("builtins.open", side_effect=Exception("Test exception")):
        with patch("pathlib.Path.exists", return_value=True):
            result = process_autoflake_results("fake_path.json")

            assert result["Status"] == "Error"
            assert "Test exception" in result["Message"]


def test_process_autoflake_results_unused_variable(sample_autoflake_results):
    """Test processing autoflake results with an unused variable."""
    # Modify the sample results to only include the unused variable
    unused_variable_issue = sample_autoflake_results["src/module/example.py"][1]
    unused_variable_result = {"src/module/example.py": [unused_variable_issue]}

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a results file with the unused variable issue
        results_file = Path(temp_dir) / "unused_variable.json"
        with open(results_file, "w") as f:
            json.dump(unused_variable_result, f)

        result = process_autoflake_results(results_file)

        assert result["Status"] == "Issues Found"
        assert result["Issue"]["code"] == "F841"
        assert "unused_var" in result["Issue"]["text"]
        assert result["Issue"]["filename"] == "src/module/example.py"
