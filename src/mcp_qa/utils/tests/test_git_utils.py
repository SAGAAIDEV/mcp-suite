"""Tests for git utility functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_qa.utils.git_utils import get_git_root


class TestGitUtils:
    """Tests for git utility functions."""

    def test_get_git_root_success(self):
        """Test successful retrieval of git root directory."""
        # Setup - mock Path.exists to simulate .git directory
        with patch("pathlib.Path.exists", return_value=True):
            # Exercise - call the function
            result = get_git_root()

            # Verify - check that the result is a Path object
            assert isinstance(result, Path)
            # The result should be the parent directory of the current file
            # since we mocked the .git directory to exist at the first check

    def test_get_git_root_not_found(self):
        """Test when git root directory cannot be found."""
        # Setup - mock Path.exists to always return False (no .git directory)
        with patch("pathlib.Path.exists", return_value=False):
            # Mock Path.parent to ensure the while loop terminates
            # by making check_dir == check_dir.parent at some point
            mock_path = MagicMock()
            mock_path.parent = mock_path

            with patch("pathlib.Path.resolve", return_value=mock_path):
                # Exercise & Verify - check that FileNotFoundError is raised
                with pytest.raises(
                    FileNotFoundError, match="Git repository root not found"
                ):
                    get_git_root()

    def test_get_git_root_found_after_traversal(self):
        """Test finding git root after traversing up multiple directories."""
        # Setup - create a mock directory structure
        mock_current_dir = MagicMock(spec=Path)
        mock_parent1 = MagicMock(spec=Path)
        mock_parent2 = MagicMock(spec=Path)
        mock_parent3 = MagicMock(spec=Path)

        # Set up the parent relationships
        mock_current_dir.parent = mock_parent1
        mock_parent1.parent = mock_parent2
        mock_parent2.parent = mock_parent3
        mock_parent3.parent = mock_parent3  # Top level, parent is self

        # Set up the __truediv__ method to return a mock .git directory
        # when path / ".git" is called
        mock_current_dir.__truediv__.return_value = MagicMock(
            spec=Path, exists=lambda: False
        )
        mock_parent1.__truediv__.return_value = MagicMock(
            spec=Path, exists=lambda: False
        )
        mock_parent2.__truediv__.return_value = MagicMock(
            spec=Path, exists=lambda: True
        )  # This one has .git
        mock_parent3.__truediv__.return_value = MagicMock(
            spec=Path, exists=lambda: False
        )

        # Patch the necessary methods
        with patch("pathlib.Path.resolve", return_value=mock_current_dir):
            # Exercise - call the function
            with patch(
                "src.mcp_suite.servers.qa.logger.debug"
            ):  # Suppress logger output
                result = get_git_root()

            # Verify - check that the result is the expected directory
            assert result == mock_parent2

    def test_get_git_root_with_real_repo(self, tmp_path):
        """Test get_git_root with a simulated git repository."""
        # Setup - create a temporary directory structure with a .git directory
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        git_dir = repo_dir / ".git"
        git_dir.mkdir()

        subdir = repo_dir / "subdir"
        subdir.mkdir()
        subsubdir = subdir / "subsubdir"
        subsubdir.mkdir()

        # Create a dummy file to simulate the location of __file__
        dummy_file = subsubdir / "dummy.py"
        dummy_file.write_text("# Dummy file")

        # Patch the __file__ attribute in the git_utils module
        with patch("mcp_suite.servers.qa.utils.git_utils.__file__", str(dummy_file)):
            # Exercise - call the function with real directory traversal
            with patch("mcp_suite.servers.qa.logger.debug"):  # Suppress logger output
                result = get_git_root()

            # Verify - check that the result is the repo directory
            assert result == repo_dir
