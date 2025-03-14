from unittest.mock import MagicMock, patch
import redis
import subprocess
import time
from src.mcp_suite.redis.server import (
    launch_redis_server,
    parse_redis_url,
    shutdown_redis_server,
)

def test_parse_redis_url_complete():
    url = "redis://:password123@localhost:6380"
    host, port, password = parse_redis_url(url)
    assert host == "localhost"
    assert port == 6380
    assert password == "password123"

def test_parse_redis_url_minimal():
    url = "redis://localhost"
    host, port, password = parse_redis_url(url)
    assert host == "localhost"
    assert port == 6379
    assert password is None

def test_parse_redis_url_invalid():
    url = "invalid-url"
    host, port, password = parse_redis_url(url)
    assert host == "localhost"
    assert port == 6379
    assert password is None

def test_parse_redis_url_no_host():
    url = "redis://:password123@"
    host, port, password = parse_redis_url(url)
    assert host == "localhost"
    assert port == 6379
    assert password == "password123"

@patch("src.mcp_suite.redis.server.redis.Redis")
@patch("src.mcp_suite.redis.server.parse_redis_url")
def test_launch_redis_server_already_running(mock_parse_url, mock_redis_class):
    mock_parse_url.return_value = ("localhost", 6379, "password")
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_redis_class.return_value = mock_client
    success, process = launch_redis_server()
    mock_redis_class.assert_called_once()
    mock_client.ping.assert_called_once()
    mock_client.close.assert_called_once()
    assert success is True
    assert process is None

@patch("src.mcp_suite.redis.server.subprocess.Popen")
@patch("src.mcp_suite.redis.server.redis.Redis")
@patch("src.mcp_suite.redis.server.parse_redis_url")
@patch("src.mcp_suite.redis.server.get_db_dir")
@patch("src.mcp_suite.redis.server.time.sleep")
def test_launch_redis_server_success(mock_sleep, mock_get_db_dir, mock_parse_url, mock_redis_class, mock_popen):
    mock_parse_url.return_value = ("localhost", 6379, "password")
    mock_client = MagicMock()
    mock_client.ping.side_effect = redis.ConnectionError("Connection refused")
    mock_redis_class.return_value = mock_client
    mock_get_db_dir.return_value = "/tmp/redis-db"
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    success, process = launch_redis_server()
    mock_popen.assert_called_once()
    assert success is True
    assert process is mock_process

@patch("src.mcp_suite.redis.server.redis_process", new_callable=MagicMock)
@patch("src.mcp_suite.redis.server.redis_launched_by_us", True)
@patch("src.mcp_suite.redis.client.redis_client")
@patch("src.mcp_suite.redis.server.logger")
def test_shutdown_redis_server_complete(mock_logger, mock_redis_client, mock_redis_process):
    mock_redis_process.poll.return_value = None
    mock_redis_process.terminate = MagicMock()
    mock_redis_process.kill = MagicMock()
    shutdown_redis_server()
    mock_redis_client.shutdown.assert_called_once_with(save=True)
    mock_redis_process.terminate.assert_called_once()
    mock_logger.success.assert_called_once_with("Redis server shutdown complete")
