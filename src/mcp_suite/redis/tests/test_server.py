"""Tests for Redis server module."""

from unittest.mock import MagicMock, patch

import redis

from src.mcp_suite.redis.server import (
    launch_redis_server,
    parse_redis_url,
    shutdown_redis_server,
)


def test_parse_redis_url_complete():
    """Test parsing a complete Redis URL."""
    url = "redis://:password123@localhost:6380"
    host, port, password = parse_redis_url(url)

    assert host == "localhost"
    assert port == 6380
    assert password == "password123"


def test_parse_redis_url_minimal():
    """Test parsing a minimal Redis URL."""
    url = "redis://localhost"
    host, port, password = parse_redis_url(url)

    assert host == "localhost"
    assert port == 6379
    assert password is None


@patch("src.mcp_suite.redis.server.redis.Redis")
@patch("src.mcp_suite.redis.server.parse_redis_url")
def test_launch_redis_server_already_running(mock_parse_url, mock_redis_class):
    """Test when Redis server is already running."""
    # Mock parse_redis_url to return test values
    mock_parse_url.return_value = ("localhost", 6379, "password")

    # Mock Redis client
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_redis_class.return_value = mock_client

    # Test launching server
    success, process = launch_redis_server()

    # Verify Redis client was created and pinged
    mock_redis_class.assert_called_once()
    mock_client.ping.assert_called_once()
    mock_client.close.assert_called_once()

    # Verify result
    assert success is True
    assert process is None


@patch("src.mcp_suite.redis.server.subprocess.Popen")
@patch("src.mcp_suite.redis.server.redis.Redis")
@patch("src.mcp_suite.redis.server.parse_redis_url")
@patch("src.mcp_suite.redis.server.get_db_dir")
@patch("src.mcp_suite.redis.server.time.sleep")
def test_launch_redis_server_success(
    mock_sleep, mock_get_db_dir, mock_parse_url, mock_redis_class, mock_popen
):
    """Test successful Redis server launch."""
    # Mock parse_redis_url to return test values
    mock_parse_url.return_value = ("localhost", 6379, "password")

    # Mock Redis client to fail on first ping (server not running)
    mock_client = MagicMock()
    mock_client.ping.side_effect = redis.ConnectionError("Connection refused")
    mock_redis_class.return_value = mock_client

    # Mock get_db_dir
    mock_get_db_dir.return_value = "/tmp/redis-db"

    # Mock subprocess.Popen
    mock_process = MagicMock()
    mock_process.poll.return_value = None  # Process is running
    mock_popen.return_value = mock_process

    # Test launching server
    success, process = launch_redis_server()

    # Verify subprocess.Popen was called with correct arguments
    mock_popen.assert_called_once()
    args = mock_popen.call_args[0][0]
    assert "redis-server" in args
    assert "--port" in args
    assert "--requirepass" in args
    assert "--appendonly" in args
    assert "--notify-keyspace-events" in args
    assert "--dir" in args

    # Verify result
    assert success is True
    assert process is mock_process


@patch("src.mcp_suite.redis.server.subprocess.Popen")
@patch("src.mcp_suite.redis.server.redis.Redis")
@patch("src.mcp_suite.redis.server.parse_redis_url")
@patch("src.mcp_suite.redis.server.get_db_dir")
@patch("src.mcp_suite.redis.server.time.sleep")
def test_launch_redis_server_process_failed(
    mock_sleep, mock_get_db_dir, mock_parse_url, mock_redis_class, mock_popen
):
    """Test Redis server launch when process fails to start."""
    # Mock parse_redis_url to return test values
    mock_parse_url.return_value = ("localhost", 6379, "password")

    # Mock Redis client to fail on ping (server not running)
    mock_client = MagicMock()
    mock_client.ping.side_effect = redis.ConnectionError("Connection refused")
    mock_redis_class.return_value = mock_client

    # Mock get_db_dir
    mock_get_db_dir.return_value = "/tmp/redis-db"

    # Mock subprocess.Popen
    mock_process = MagicMock()
    mock_process.poll.return_value = 1  # Process exited with error
    mock_process.communicate.return_value = ("", "Error starting Redis")
    mock_popen.return_value = mock_process

    # Test launching server
    success, process = launch_redis_server()

    # Verify result
    assert success is False
    assert process is None


@patch("src.mcp_suite.redis.server.subprocess.Popen")
@patch("src.mcp_suite.redis.server.redis.Redis")
@patch("src.mcp_suite.redis.server.parse_redis_url")
def test_launch_redis_server_exception(mock_parse_url, mock_redis_class, mock_popen):
    """Test Redis server launch with exception."""
    # Mock parse_redis_url to return test values
    mock_parse_url.return_value = ("localhost", 6379, "password")

    # Mock Redis client to fail on ping (server not running)
    mock_client = MagicMock()
    mock_client.ping.side_effect = redis.ConnectionError("Connection refused")
    mock_redis_class.return_value = mock_client

    # Mock subprocess.Popen to raise exception
    mock_popen.side_effect = Exception("Failed to launch process")

    # Test launching server
    success, process = launch_redis_server()

    # Verify result
    assert success is False
    assert process is None


@patch("src.mcp_suite.redis.server.redis_process", new_callable=MagicMock)
@patch("src.mcp_suite.redis.server.redis_launched_by_us", True)
@patch("src.mcp_suite.redis.client.redis_client")
def test_shutdown_redis_server_success(mock_redis_client, mock_redis_process):
    """Test successful Redis server shutdown."""
    # Mock process
    mock_process = MagicMock()
    mock_process.poll.return_value = None  # Process is running

    # Set the mock_redis_process to be the actual process
    mock_redis_process.__bool__.return_value = True  # Make it truthy
    mock_redis_process.poll.return_value = None  # Process is running
    mock_redis_process.terminate = MagicMock()  # Add terminate method

    # Test shutdown
    shutdown_redis_server()

    # Verify client.shutdown was called
    mock_redis_client.shutdown.assert_called_once_with(save=True)

    # Verify process.terminate was called
    mock_redis_process.terminate.assert_called_once()


@patch("src.mcp_suite.redis.server.redis_process", new_callable=MagicMock)
@patch("src.mcp_suite.redis.server.redis_launched_by_us", True)
@patch("src.mcp_suite.redis.client.redis_client")
@patch("src.mcp_suite.redis.server.time.sleep")
def test_shutdown_redis_server_force_kill(
    mock_sleep, mock_redis_client, mock_redis_process
):
    """Test Redis server shutdown with force kill."""
    # Set up the mock_redis_process
    mock_redis_process.__bool__.return_value = True  # Make it truthy
    mock_redis_process.poll.side_effect = [
        None,
        None,
    ]  # Process still running after terminate
    mock_redis_process.terminate = MagicMock()  # Add terminate method
    mock_redis_process.kill = MagicMock()  # Add kill method

    # Mock client to raise exception on shutdown
    mock_redis_client.shutdown.side_effect = Exception("Shutdown error")

    # Test shutdown
    shutdown_redis_server()

    # Verify process.terminate and kill were called
    mock_redis_process.terminate.assert_called_once()
    mock_redis_process.kill.assert_called_once()


@patch("src.mcp_suite.redis.server.redis_process")
@patch("src.mcp_suite.redis.server.redis_launched_by_us", False)
def test_shutdown_redis_server_not_launched_by_us(mock_redis_process):
    """Test Redis server shutdown when not launched by us."""
    # Test shutdown
    shutdown_redis_server()

    # Verify process methods were not called
    mock_redis_process.assert_not_called()


@patch("src.mcp_suite.redis.server.redis_process", None)
@patch("src.mcp_suite.redis.server.redis_launched_by_us", True)
def test_shutdown_redis_server_no_process():
    """Test Redis server shutdown when process is None."""
    # Test shutdown
    shutdown_redis_server()
    # No exception should be raised


@patch("src.mcp_suite.redis.server.redis_process", new_callable=MagicMock)
@patch("src.mcp_suite.redis.server.redis_launched_by_us", True)
@patch("src.mcp_suite.redis.client.redis_client")
@patch("src.mcp_suite.redis.server.logger")
def test_shutdown_redis_server_exception(
    mock_logger, mock_redis_client, mock_redis_process
):
    """Test Redis server shutdown with an exception during the process."""
    # Set up the mock_redis_process
    mock_redis_process.__bool__.return_value = True  # Make it truthy

    # Make poll raise an exception to trigger the error handling
    mock_redis_process.poll.side_effect = Exception("Test exception")

    # Test shutdown
    from src.mcp_suite.redis.server import shutdown_redis_server

    shutdown_redis_server()

    # Verify error was logged
    mock_logger.error.assert_called_once()

    # We can't directly verify the global variables were reset since they're mocked
    # But we can verify the error message was logged with the exception
    error_message = mock_logger.error.call_args[0][0]
    assert "Error shutting down Redis server" in error_message
