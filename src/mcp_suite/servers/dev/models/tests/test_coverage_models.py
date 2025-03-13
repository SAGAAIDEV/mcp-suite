"""Tests for coverage models."""

import pytest

from src.mcp_suite.servers.dev.models.coverage_models import (
    BranchCoverage,
    CoverageIssue,
)


class TestBranchCoverage:
    """Tests for the BranchCoverage class."""

    def test_init(self):
        """Test initialization of BranchCoverage."""
        branch = BranchCoverage(source=1, target=2)
        assert branch.source == 1
        assert branch.target == 2

    def test_str(self):
        """Test string representation."""
        branch = BranchCoverage(source=1, target=2)
        assert str(branch) == "1 -> 2"

        branch = BranchCoverage(source="a", target="b")
        assert str(branch) == "a -> b"

    def test_from_list(self):
        """Test creating from a list."""
        branch = BranchCoverage.from_list([1, 2])
        assert branch.source == 1
        assert branch.target == 2

        branch = BranchCoverage.from_list(["a", "b"])
        assert branch.source == "a"
        assert branch.target == "b"

    def test_from_list_invalid(self):
        """Test creating from an invalid list."""
        with pytest.raises(
            ValueError, match="Branch list must have exactly 2 elements"
        ):
            BranchCoverage.from_list([1])

        with pytest.raises(
            ValueError, match="Branch list must have exactly 2 elements"
        ):
            BranchCoverage.from_list([1, 2, 3])

    def test_to_list(self):
        """Test converting to a list."""
        branch = BranchCoverage(source=1, target=2)
        assert branch.to_list() == [1, 2]

        branch = BranchCoverage(source="a", target="b")
        assert branch.to_list() == ["a", "b"]


class TestCoverageIssue:
    """Tests for the CoverageIssue class."""

    def test_init(self):
        """Test initialization of CoverageIssue."""
        issue = CoverageIssue(
            file_path="file.py",
            section_name="function",
            missing_lines=[1, 2, 3],
            missing_branches=[BranchCoverage(source=1, target=2)],
        )
        assert issue.file_path == "file.py"
        assert issue.section_name == "function"
        assert issue.missing_lines == [1, 2, 3]
        assert len(issue.missing_branches) == 1
        assert issue.missing_branches[0].source == 1
        assert issue.missing_branches[0].target == 2

    def test_init_optional_fields(self):
        """Test initialization with optional fields."""
        issue = CoverageIssue(file_path="file.py", section_name="function")
        assert issue.file_path == "file.py"
        assert issue.section_name == "function"
        assert issue.missing_lines is None
        assert issue.missing_branches is None

    def test_str(self):
        """Test string representation."""
        issue = CoverageIssue(
            file_path="file.py",
            section_name="function",
            missing_lines=[1, 2, 3],
            missing_branches=[BranchCoverage(source=1, target=2)],
        )
        expected = (
            "file.py:function\n"
            "  Missing lines: [1, 2, 3]\n"
            "  Missing branches: 1\n"
            "    1 -> 2\n"
        )
        assert str(issue) == expected

    def test_str_no_missing(self):
        """Test string representation with no missing lines or branches."""
        issue = CoverageIssue(file_path="file.py", section_name="function")
        expected = "file.py:function\n"
        assert str(issue) == expected

    def test_from_dict(self):
        """Test creating from a dictionary."""
        key = "file.py:function"
        data = {
            "missing_lines": [1, 2, 3],
            "missing_branches": [[1, 2], [3, 4]],
        }
        issue = CoverageIssue.from_dict(key, data)
        assert issue.file_path == "file.py"
        assert issue.section_name == "function"
        assert issue.missing_lines == [1, 2, 3]
        assert len(issue.missing_branches) == 2
        assert issue.missing_branches[0].source == 1
        assert issue.missing_branches[0].target == 2
        assert issue.missing_branches[1].source == 3
        assert issue.missing_branches[1].target == 4

    def test_from_dict_no_missing(self):
        """Test creating from a dictionary with no missing lines or branches."""
        key = "file.py:function"
        data = {}
        issue = CoverageIssue.from_dict(key, data)
        assert issue.file_path == "file.py"
        assert issue.section_name == "function"
        assert issue.missing_lines is None
        assert issue.missing_branches is None

    def test_from_dict_with_branch_objects(self):
        """Test creating from a dictionary with branch objects."""
        key = "file.py:function"
        branch = BranchCoverage(source=1, target=2)
        data = {
            "missing_branches": [branch],
        }
        issue = CoverageIssue.from_dict(key, data)
        assert issue.file_path == "file.py"
        assert issue.section_name == "function"
        assert len(issue.missing_branches) == 1
        assert issue.missing_branches[0] is branch  # Should be the same object

    def test_to_dict_entry(self):
        """Test converting to a dictionary entry."""
        issue = CoverageIssue(
            file_path="file.py",
            section_name="function",
            missing_lines=[1, 2, 3],
            missing_branches=[
                BranchCoverage(source=1, target=2),
                BranchCoverage(source=3, target=4),
            ],
        )
        key, value = issue.to_dict_entry()
        assert key == "file.py:function"
        assert value["missing_lines"] == [1, 2, 3]
        assert value["missing_branches"] == [[1, 2], [3, 4]]

    def test_to_dict_entry_no_missing(self):
        """Test converting to a dictionary entry with no missing lines or branches."""
        issue = CoverageIssue(file_path="file.py", section_name="function")
        key, value = issue.to_dict_entry()
        assert key == "file.py:function"
        assert value == {}

    def test_len(self):
        """Test the __len__ method."""
        # Test with both missing lines and branches
        issue = CoverageIssue(
            file_path="file.py",
            section_name="function",
            missing_lines=[1, 2, 3],
            missing_branches=[BranchCoverage(source=1, target=2)],
        )
        assert len(issue) == 4  # 3 lines + 1 branch

        # Test with only missing lines
        issue = CoverageIssue(
            file_path="file.py",
            section_name="function",
            missing_lines=[1, 2, 3],
        )
        assert len(issue) == 3

        # Test with only missing branches
        issue = CoverageIssue(
            file_path="file.py",
            section_name="function",
            missing_branches=[BranchCoverage(source=1, target=2)],
        )
        assert len(issue) == 1

        # Test with no missing lines or branches
        issue = CoverageIssue(file_path="file.py", section_name="function")
        assert len(issue) == 0
