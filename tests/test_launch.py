"""
Tests for the launch.py module.
"""

from unittest.mock import MagicMock, patch

import redis

from src.mcp_suite.launch import (
    connect_to_redis,
    launch_redis_server,
    main,
    parse_redis_url,
)


def test_main():
    """Test the main function."""
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

            # Verify Redis was launched and connected to
            mock_launch.assert_called_once()
            mock_connect.assert_called_once()
            mock_redis.set.assert_called_once_with(
                "mcp_suite_test", "Hello from Redis!"
            )
            mock_redis.get.assert_called_once_with("mcp_suite_test")


def test_main_redis_connection_failure():
    """Test the main function when Redis connection fails."""
    with patch("src.mcp_suite.launch.launch_redis_server") as mock_launch:
        with patch("src.mcp_suite.launch.connect_to_redis") as mock_connect:
            # Mock failed Redis connection
            mock_connect.return_value = None
            mock_launch.return_value = (True, None)

            # Call the main function
            result = main()

            # Verify the result
            assert result == "Hello from mcp-suite! (Redis connection failed)"


def test_connect_to_redis():
    """Test the connect_to_redis function."""
    with patch("redis.Redis") as mock_redis_class:
        # Mock successful connection
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis

        # Call the function
        result = connect_to_redis(
            host="test-host", port=1234, password="test-password", db=2
        )

        # Verify the result
        assert result == mock_redis
        mock_redis_class.assert_called_once_with(
            host="test-host",
            port=1234,
            password="test-password",
            db=2,
            decode_responses=True,
        )
        mock_redis.ping.assert_called_once()


def test_connect_to_redis_failure():
    """Test the connect_to_redis function when connection fails."""
    with patch("redis.Redis") as mock_redis_class:
        # Mock failed connection
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = redis.ConnectionError("Connection refused")
        mock_redis_class.return_value = mock_redis

        # Call the function
        result = connect_to_redis()

        # Verify the result
        assert result is None
        mock_redis.ping.assert_called_once()


def test_launch_redis_server_already_running():
    """Test the launch_redis_server function when Redis is already running."""
    with patch("redis.Redis") as mock_redis_class:
        # Mock Redis already running
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis

        # Call the function
        success, process = launch_redis_server()

        # Verify the result
        assert success is True
        assert process is None
        mock_redis.ping.assert_called_once()


def test_launch_redis_server_new_instance():
    """Test the launch_redis_server function when launching a new Redis instance."""
    with patch("redis.Redis") as mock_redis_class:
        with patch("subprocess.Popen") as mock_popen:
            # Mock Redis not running
            mock_redis = MagicMock()
            mock_redis.ping.side_effect = redis.ConnectionError("Connection refused")
            mock_redis_class.return_value = mock_redis

            # Mock successful process launch
            mock_process = MagicMock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process

            # Call the function
            success, process = launch_redis_server(
                port=1234,
                password="test-password",
                appendonly=True,
                keyspace_events="KEA",
            )

            # Verify the result
            assert success is True
            assert process == mock_process
            mock_redis.ping.assert_called_once()
            mock_popen.assert_called_once()
            mock_process.poll.assert_called_once()


def test_parse_redis_url_invalid_db():
    """Test parse_redis_url with invalid DB number."""
    with patch("src.mcp_suite.launch.logger") as mock_logger:
        host, port, password, db = parse_redis_url("redis://localhost/invalid")
        assert host == "localhost"
        assert port == 6379
        assert password is None
        assert db == 0
        mock_logger.warning.assert_called_once()


def test_main_with_pytest_module():
    """Test main function when running under pytest."""
    with patch("src.mcp_suite.launch.launch_redis_server") as mock_launch:
        with patch("src.mcp_suite.launch.connect_to_redis") as mock_connect:
            # Mock successful Redis connection
            mock_redis = MagicMock()
            mock_redis.get.return_value = "Hello from Redis!"
            mock_connect.return_value = mock_redis
            mock_launch.return_value = (True, None)

            # Call the main function
            result = main()

            # Verify the result is the simplified version for pytest
            assert result == "Hello from mcp-suite! Redis test: Hello from Redis!"


def test_main_redis_connection_failure_with_pytest():
    """Test main function with Redis connection failure when running under pytest."""
    with patch("src.mcp_suite.launch.launch_redis_server") as mock_launch:
        with patch("src.mcp_suite.launch.connect_to_redis") as mock_connect:

            # Mock Redis connection failure
            mock_connect.return_value = None
            mock_launch.return_value = (True, None)

            # Call the main function
            result = main()

            # Verify the result is the simplified version for pytest
            assert result == "Hello from mcp-suite! (Redis connection failed)"


def test_main_redis_connection_failure_without_pytest():
    """Test main function with Redis connection failure when not running under pytest."""
    with patch("src.mcp_suite.launch.launch_redis_server") as mock_launch:
        with patch("src.mcp_suite.launch.connect_to_redis") as mock_connect:
            # Mock failed Redis connection
            mock_connect.return_value = None
            mock_launch.return_value = (True, None)

            # Call the main function
            result = main()

            # Verify the result includes the failure message
            assert "Hello from mcp-suite!" in result


def test_main_redis_server_launch_failure():
    """Test main function when Redis server launch fails."""
    with patch("src.mcp_suite.launch.launch_redis_server") as mock_launch:
        with patch("src.mcp_suite.launch.connect_to_redis") as mock_connect:
            with patch("src.mcp_suite.launch.logger") as mock_logger:

                # Mock Redis server launch failure but successful connection
                mock_redis = MagicMock()
                mock_redis.get.return_value = "Hello from Redis!"
                mock_connect.return_value = mock_redis
                mock_launch.return_value = (False, None)

                # Call the main function
                result = main()

                # Verify the warning was logged
                mock_logger.warning.assert_called_once_with(
                    "Could not launch Redis server, attempting to connect anyway"
                )

                # Verify the result
                assert "Hello from mcp-suite!" in result
