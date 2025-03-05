"""Tests for the core module."""

# mypy: ignore-errors

from src.mcp_suite.core import main


def test_main() -> None:
    """Test that the main function returns the expected output."""
    result = main()
    assert result == "Hello from mcp-suite!"
