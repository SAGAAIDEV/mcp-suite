"""
Tests for the launch.py module.
"""

from src.mcp_suite.launch import main


def test_main():
    """Test the main function."""
    result = main()
    assert result == "Hello from mcp-suite!"
    assert isinstance(result, str)
