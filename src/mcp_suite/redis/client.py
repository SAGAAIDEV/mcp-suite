import redis
import subprocess
from unittest.mock import MagicMock, patch

import pytest

# Import directly the functions under test
from src.mcp_suite.redis.server import (
    launch_redis_server,
    parse_redis_url,
    shutdown_redis_server,
)


@pytest.fixture(autouse=True)
def mock_config_env_module(monkeypatch):
    mock_redis_env = MagicMock()
    mock_redis_env.URL = "redis://:testpassword@localhost:6379"
    mock_env = MagicMock(REDIS=mock_redis_env)
    mock_redis_env = MagicMock(URL="redis://:testpassword@localhost:6379")
    with patch.dict("sys.modules", {"src.config.env": mock_env}):
        yield


@pytest.fixture
def mock_redis_client():
    with patch("redis.Redis") as mock_redis:
        instance = MagicMock()
        instance.ping.return_value = True
        mock_redis.return_value = mock_redis
        yield mock_redis


@pytest.fixture
def mock_popen_success():
    mock_proc = MagicMock(spec=subprocess.Popen)
    mock_proc_attrs = {"poll.return_value": None, "communicate.return_value": ("", "")}
    mock_proc = MagicMock(**mock_proc_attrs)
    with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
        yield mock_popen


def test_parse_redis_url():
    url = "redis://:mypassword@127.0.0.1:6380"
    host, port, password = parse_redis_url(url)
    assert host == "127.0.0.1"
    assert port == 6380
    assert password == "mypassword"


def test_parse_redis_url_defaults():
    url = "redis://localhost"
    host, port, password = parse_redis_url(url)
    assert host == "localhost"
    assert port == 6379
    assert password is None


def test_launch_redis_server_already_running(mock_redis_client):
    mock_redis_instance = mock_redis_client.return_value
    mock_redis_instance.ping.return_value = True

    success, process = launch_redis_server(port=6379, password="redispassword")
    assert success is True
    assert process is None


def test_launch_redis_server_new_instance(mock_redis_client, mock_popen_success):
    # Simulate Redis not running initially
    mock_redis_client.return_value.ping.side_effect = redis.ConnectionError()

    success, process = launch_redis_server(port=6380, password="testpass")
    assert success is True
    assert process is not None
    mock_popen_success.assert_called_once()


def test_launch_redis_server_failure(mock_redis_client):
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 1  # Non-zero means process failed immediately
        mock_proc.communicate.return_value = ("", "Error starting Redis")
        mock_popen.return_value = mock_proc

        success, process = launch_redis_server()
        assert success is False
        assert process is None


def test_shutdown_redis_server(mock_redis_client, mock_redis_popen_success):
    global redis_process, redis_launched_by_us
    redis_process = mock_redis_popen_success.return_value
    redis_launched_by_us = True

    shutdown_redis_server()

    redis_process.terminate.assert_called_once()
    assert redis_process is None
