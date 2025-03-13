"""Tests for the core module."""

# mypy: ignore-errors

from unittest.mock import patch

from src.mcp_suite.launch import main


def test_main() -> None:
    """Test that the main function returns the expected output."""
    with patch("src.mcp_suite.launch.logger") as mock_logger:
        with patch("src.mcp_suite.launch.setup_directories") as mock_setup_directories:
            with patch(
                "src.mcp_suite.launch.configure_logger"
            ) as mock_configure_logger:
                # Call the main function
                result = main()

                # Verify the result
                assert (
                    result
                    == "Hello from mcp-suite! (Redis functionality has been restructured)"
                )

                # Verify logger was called
                mock_logger.info.assert_any_call(
                    "Redis functionality has been removed or restructured"
                )

                # Verify setup_directories was called
                mock_setup_directories.assert_called_once()

                # Verify configure_logger was called
                mock_configure_logger.assert_called_once()
