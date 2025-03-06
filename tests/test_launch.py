"""Test the launch module."""

from mcp_suite.launch import main


def test_main():
    """Test the main function."""
    result = main()
    assert result == "Hello from mcp-suite!"
