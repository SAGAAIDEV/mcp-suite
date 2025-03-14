"""Tests for the Redis Manager module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import redis

from mcp_suite.base.redis.redis_manager import RedisManager


@pytest.fixture
def redis_manager():
    """Fixture to provide a fresh RedisManager instance for each test."""
    # Reset the singleton instance before each test
    RedisManager.reset_instance()
    manager = RedisManager()
    yield manager
    # Clean up after each test
    manager.close_redis_connection()
    if manager.process is not None:
        manager.process = None
    manager.launched_by_us = False


class TestRedisManager:
    """Test cases for the RedisManager class."""

    def test_singleton_pattern(self):
        """Test that RedisManager follows the singleton pattern."""
        # Create two instances
        manager1 = RedisManager()
        manager2 = RedisManager()

        # They should be the same object
        assert manager1 is manager2

        # Reset for other tests
        RedisManager.reset_instance()

    def test_parse_redis_url(self, redis_manager):
        """Test parsing Redis URLs into connection parameters."""
        # Test with full URL
        host, port, password, db = redis_manager.parse_redis_url(
            "redis://:password@localhost:6380/2"
        )
        assert host == "localhost"
        assert port == 6380
        assert password == "password"
        assert db == 2

        # Test with minimal URL
        host, port, password, db = redis_manager.parse_redis_url("redis://localhost")
        assert host == "localhost"
        assert port == 6379
        assert password is None
        assert db == 0

        # Test with invalid DB number
        host, port, password, db = redis_manager.parse_redis_url(
            "redis://localhost/invalid"
        )
        assert host == "localhost"
        assert port == 6379
        assert password is None
        assert db == 0

    @patch("redis.Redis")
    def test_connect_to_redis_success(self, mock_redis, redis_manager):
        """Test successful connection to Redis."""
        # Setup mock
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        # Call the method
        result = redis_manager.connect_to_redis(
            host="testhost", port=1234, password="testpass", db=3
        )

        # Verify the result
        assert result is mock_client
        assert redis_manager.client is mock_client

        # Verify Redis was created with correct parameters
        mock_redis.assert_called_once_with(
            host="testhost",
            port=1234,
            password="testpass",
            db=3,
            decode_responses=True,
        )
        mock_client.ping.assert_called_once()

    @patch("redis.Redis")
    def test_connect_to_redis_failure(self, mock_redis, redis_manager):
        """Test failed connection to Redis."""
        # Setup mock to raise an exception
        mock_redis.return_value.ping.side_effect = redis.ConnectionError("Test error")

        # Call the method
        result = redis_manager.connect_to_redis()

        # Verify the result
        assert result is None
        assert redis_manager.client is None

    @patch("redis.Redis")
    @patch("subprocess.Popen")
    @patch("time.sleep")
    def test_launch_redis_server_already_running(
        self, mock_sleep, mock_popen, mock_redis, redis_manager
    ):
        """Test launching Redis server when it's already running."""
        # Setup mock
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        # Call the method
        success, process = redis_manager.launch_redis_server(
            port=1234, password="testpass"
        )

        # Verify the result
        assert success is True
        assert process is None
        assert redis_manager.launched_by_us is False

        # Verify Redis client was created and pinged
        mock_redis.assert_called_once()
        mock_client.ping.assert_called_once()
        mock_client.close.assert_called_once()

        # Verify subprocess was not called
        mock_popen.assert_not_called()

    @patch("redis.Redis")
    @patch("subprocess.Popen")
    @patch("time.sleep")
    @patch("mcp_suite.base.redis.redis_manager.get_db_dir")
    def test_launch_redis_server_success(
        self, mock_get_db_dir, mock_sleep, mock_popen, mock_redis, redis_manager
    ):
        """Test successfully launching Redis server."""
        # Setup mocks
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.side_effect = [redis.ConnectionError(), MagicMock()]

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        mock_get_db_dir.return_value = Path("/test/db/dir")

        # Call the method
        success, process = redis_manager.launch_redis_server(
            port=1234, password="testpass"
        )

        # Verify the result
        assert success is True
        assert process is mock_process
        assert redis_manager.process is mock_process
        assert redis_manager.launched_by_us is True

        # Verify subprocess was called with correct arguments
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == "redis-server"
        assert "--port" in args
        assert "1234" in args
        assert "--requirepass" in args
        assert "testpass" in args
        assert "--appendonly" in args
        assert "yes" in args
        assert "--dir" in args
        assert "/test/db/dir" in str(args)

    @patch("redis.Redis")
    @patch("subprocess.Popen")
    @patch("time.sleep")
    def test_launch_redis_server_failure(
        self, mock_sleep, mock_popen, mock_redis, redis_manager
    ):
        """Test failed launch of Redis server."""
        # Setup mocks
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.side_effect = redis.ConnectionError()

        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process exited with error
        mock_process.communicate.return_value = ("", "Error starting Redis")
        mock_popen.return_value = mock_process

        # Call the method
        success, process = redis_manager.launch_redis_server()

        # Verify the result
        assert success is False
        assert process is None
        assert redis_manager.process is None
        assert redis_manager.launched_by_us is False

    @patch("redis.Redis")
    def test_shutdown_redis_server_not_launched_by_us(self, mock_redis, redis_manager):
        """Test shutdown when Redis was not launched by us."""
        # Setup
        redis_manager.process = MagicMock()
        redis_manager.launched_by_us = False

        # Call the method
        redis_manager.shutdown_redis_server()

        # Verify process was not terminated
        redis_manager.process.terminate.assert_not_called()
        assert redis_manager.process is not None

    @patch("time.sleep")
    def test_shutdown_redis_server_success(self, mock_sleep, redis_manager):
        """Test successful shutdown of Redis server."""
        # Setup
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        redis_manager.process = mock_process
        redis_manager.launched_by_us = True
        redis_manager.client = MagicMock()

        # Call the method
        redis_manager.shutdown_redis_server()

        # Verify client shutdown was attempted
        redis_manager.client.shutdown.assert_called_once_with(save=True)

        # Verify process was terminated
        mock_process.terminate.assert_called_once()

        # Verify instance variables were reset
        assert redis_manager.process is None
        assert redis_manager.launched_by_us is False

    def test_shutdown_redis_server_with_force_kill(self, redis_manager):
        """Test shutdown with force kill if terminate doesn't work."""
        # Setup
        mock_process = MagicMock()
        # First poll returns None (still running),
        # second poll also returns None (still running after terminate)
        mock_process.poll.side_effect = [None, None]
        redis_manager.process = mock_process
        redis_manager.launched_by_us = True
        redis_manager.client = MagicMock()
        redis_manager.client.shutdown.side_effect = Exception("Test exception")

        # Call the method
        redis_manager.shutdown_redis_server()

        # Verify process was terminated and then killed
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    def test_close_redis_connection(self, redis_manager):
        """Test closing Redis client connection."""
        # Setup
        mock_client = MagicMock()
        redis_manager.client = mock_client

        # Call the method
        redis_manager.close_redis_connection()

        # Verify client was closed
        mock_client.close.assert_called_once()
        assert redis_manager.client is None

    def test_close_redis_connection_no_client(self, redis_manager):
        """Test closing Redis connection when no client exists."""
        # Setup
        redis_manager.client = None

        # Call the method - should not raise an exception
        redis_manager.close_redis_connection()

    @patch.object(RedisManager, "connect_to_redis")
    def test_get_client_existing(self, mock_connect, redis_manager):
        """Test getting existing Redis client."""
        # Setup
        mock_client = MagicMock()
        redis_manager.client = mock_client

        # Call the method
        result = redis_manager.get_client()

        # Verify result and that connect was not called
        assert result is mock_client
        mock_connect.assert_not_called()

    @patch.object(RedisManager, "connect_to_redis")
    def test_get_client_new(self, mock_connect, redis_manager):
        """Test getting new Redis client."""
        # Setup
        mock_client = MagicMock()

        # Configure the mock to set redis_manager.client when called
        def side_effect(*args, **kwargs):
            redis_manager.client = mock_client
            return mock_client

        mock_connect.side_effect = side_effect
        redis_manager.client = None

        # Call the method
        result = redis_manager.get_client()

        # Verify connect was called and result is correct
        mock_connect.assert_called_once()
        assert result is mock_client

    @patch.object(RedisManager, "get_client")
    @patch.object(RedisManager, "launch_redis_server")
    @patch.object(RedisManager, "connect_to_redis")
    def test_ensure_redis_running_already_connected(
        self, mock_connect, mock_launch, mock_get_client, redis_manager
    ):
        """Test ensuring Redis is running when already connected."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Call the method
        result = redis_manager.ensure_redis_running()

        # Verify result and that launch was not called
        assert result is True
        mock_get_client.assert_called_once()
        mock_launch.assert_not_called()
        mock_connect.assert_not_called()

    @patch.object(RedisManager, "get_client")
    @patch.object(RedisManager, "launch_redis_server")
    @patch.object(RedisManager, "connect_to_redis")
    def test_ensure_redis_running_launch_success(
        self, mock_connect, mock_launch, mock_get_client, redis_manager
    ):
        """Test ensuring Redis is running with successful launch."""
        # Setup
        mock_get_client.return_value = None
        mock_launch.return_value = (True, MagicMock())
        mock_connect.return_value = MagicMock()

        # Call the method
        result = redis_manager.ensure_redis_running()

        # Verify result and method calls
        assert result is True
        mock_get_client.assert_called_once()
        mock_launch.assert_called_once()
        mock_connect.assert_called_once()

    @patch.object(RedisManager, "get_client")
    @patch.object(RedisManager, "launch_redis_server")
    def test_ensure_redis_running_launch_failure(
        self, mock_launch, mock_get_client, redis_manager
    ):
        """Test ensuring Redis is running with failed launch."""
        # Setup
        mock_get_client.return_value = None
        mock_launch.return_value = (False, None)

        # Call the method
        result = redis_manager.ensure_redis_running()

        # Verify result
        assert result is False
        mock_get_client.assert_called_once()
        mock_launch.assert_called_once()

    @patch.object(RedisManager, "get_client")
    def test_ensure_redis_running_exception(self, mock_get_client, redis_manager):
        """Test ensuring Redis is running with exception."""
        # Setup
        mock_get_client.side_effect = Exception("Test exception")

        # Call the method
        result = redis_manager.ensure_redis_running()

        # Verify result
        assert result is False
        mock_get_client.assert_called_once()

    @patch("subprocess.Popen")
    @patch("redis.Redis")
    def test_launch_redis_server_general_exception(
        self, mock_redis, mock_popen, redis_manager
    ):
        """Test launch_redis_server with a general exception."""
        # Setup Redis mock to raise ConnectionError to simulate Redis not running
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.side_effect = redis.ConnectionError(
            "Connection refused"
        )
        mock_redis.return_value = mock_redis_instance

        # Setup Popen mock to raise an exception
        mock_popen.side_effect = Exception("Test general exception")

        # Call the method
        success, process = redis_manager.launch_redis_server()

        # Verify the result
        assert success is False
        assert process is None
        assert redis_manager.process is None
        assert redis_manager.launched_by_us is False

    def test_shutdown_redis_server_with_exception(self, redis_manager):
        """Test shutdown_redis_server with an exception."""
        # Setup
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.terminate.side_effect = Exception("Test shutdown exception")
        redis_manager.process = mock_process
        redis_manager.launched_by_us = True
        redis_manager.client = None

        # Call the method
        redis_manager.shutdown_redis_server()

        # Verify instance variables were reset despite the exception
        assert redis_manager.process is None
        assert redis_manager.launched_by_us is False

    def test_close_redis_connection_with_exception(self, redis_manager):
        """Test close_redis_connection with an exception."""
        # Setup
        mock_client = MagicMock()
        mock_client.close.side_effect = Exception("Test close exception")
        redis_manager.client = mock_client

        # Call the method - should not raise an exception
        redis_manager.close_redis_connection()

        # Verify client is still set to the mock client when an exception occurs
        assert redis_manager.client is mock_client
