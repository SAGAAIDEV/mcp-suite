"""Tests for the core module."""

# mypy: ignore-errors

from unittest.mock import MagicMock, patch

from src.mcp_suite.launch import main


def test_main() -> None:
    """Test that the main function returns the expected output."""
    with patch("src.mcp_suite.launch.launch_redis_server") as mock_launch:
        with patch("src.mcp_suite.launch.connect_to_redis") as mock_connect:
            # Mock successful Redis connection
            mock_redis = MagicMock()
            mock_redis.get.return_value = "Hello from Redis!"
            mock_connect.return_value = mock_redis
            mock_launch.return_value = (True, None)

            # Call the main function
            result = main()

            # Verify the result
            assert result == "Hello from mcp-suite! Redis test: Hello from Redis!"
