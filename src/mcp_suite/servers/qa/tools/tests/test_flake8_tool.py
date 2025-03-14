"""Tests for the flake8 tool."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_suite.servers.qa.tools.flake8_tool import run_flake8


class TestFlake8Tool:
    """Test cases for the flake8 tool."""

    @pytest.mark.asyncio
    @patch("mcp_suite.servers.qa.tools.flake8_tool.process_flake8_results")
    @patch("subprocess.run")
    @patch("mcp_suite.servers.qa.tools.flake8_tool.get_git_root")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.unlink")
    async def test_run_flake8_success(
        self,
        mock_unlink,
        mock_exists,
        mock_mkdir,
        mock_get_git_root,
        mock_run,
        mock_process_results,
    ):
        """Test successful execution of flake8."""
        # Setup mocks
        mock_git_root = MagicMock()
        mock_get_git_root.return_value = mock_git_root
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        # Setup the mock to return a success result
        expected_result = {
            "Status": "Success",
            "Message": "No issues found.",
        }
        mock_process_results.return_value = expected_result

        # Call the function
        result = await run_flake8("test_path")

        # Verify the result matches what the mock returns
        assert result == expected_result

    @pytest.mark.asyncio
    @patch("mcp_suite.servers.qa.tools.flake8_tool.process_flake8_results")
    @patch("subprocess.run")
    @patch("mcp_suite.servers.qa.tools.flake8_tool.get_git_root")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.unlink")
    async def test_run_flake8_with_default_path(
        self,
        mock_unlink,
        mock_exists,
        mock_mkdir,
        mock_get_git_root,
        mock_run,
        mock_process_results,
    ):
        """Test flake8 execution with default path (.)."""
        # Setup mocks
        mock_git_root = MagicMock()
        mock_get_git_root.return_value = mock_git_root
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        # Setup the mock to return a success result
        expected_result = {
            "Status": "Success",
            "Message": "No issues found.",
        }
        mock_process_results.return_value = expected_result

        # Call the function with explicit "." path to cover the else branch
        result = await run_flake8(file_path=".")

        # Verify the result matches what the mock returns
        assert result == expected_result

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("mcp_suite.servers.qa.tools.flake8_tool.get_git_root")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.unlink")
    async def test_run_flake8_error(
        self, mock_unlink, mock_exists, mock_mkdir, mock_get_git_root, mock_run
    ):
        """Test flake8 execution with an error."""
        # Setup mocks
        mock_get_git_root.return_value = MagicMock()
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1, stderr="No such file or directory"
        )

        # Call the function
        result = await run_flake8("test_path")

        # Verify the result
        assert result["Status"] == "Error"
        assert "Message" in result
        assert "Instructions" in result
