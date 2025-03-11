import sys
from unittest.mock import MagicMock, patch
import os
from pathlib import Path

# --- First, set environment variables ---
os.environ["REDDIT_CLIENT_ID"] = "dummy_client_id"
os.environ["REDDIT_CLIENT_SECRET"] = "dummy_client_secret"
os.environ["LLM_OPENAI_API_KEY"] = "dummy_openai_key"
os.environ["LLM_ANTHROPIC_API_KEY"] = "dummy_anthropic_key"
os.environ["LLM_GEMINI_API_KEY"] = "dummy_gemini_key"

# --- Block actual imports by completely bypassing the normal import chain ---

# 1. Block the src.mcp_suite.redis module and its submodules
sys.modules["src.mcp_suite.redis.client"] = MagicMock()
sys.modules["src.mcp_suite.redis.server"] = MagicMock()
sys.modules["src.mcp_suite.redis.utils"] = MagicMock()

# 2. Block external modules
sys.modules["redis"] = MagicMock()
sys.modules["loguru"] = MagicMock()

# 3. Create mock classes for Pydantic models
class MockLLM:
    OPENAI_API_KEY = "dummy_openai_key"
    ANTHROPIC_API_KEY = "dummy_anthropic_key"
    GEMINI_API_KEY = "dummy_gemini_key"

class MockReddit:
    CLIENT_ID = "dummy_client_id"
    CLIENT_SECRET = "dummy_client_secret"

class MockRedisConfig:
    URL = "redis://localhost:6379"
    DB_PATH = "/tmp/redis-db"

# 4. Mock the config.env module completely
env_mock = MagicMock()
env_mock.REDIS = MockRedisConfig()
env_mock.REDDIT = MockReddit()
env_mock.LLM = MockLLM()
env_mock.LLM_API_KEYS = MockLLM()
sys.modules["src.config.env"] = env_mock

# 5. Block pydantic modules to prevent validation errors
sys.modules["pydantic"] = MagicMock()
sys.modules["pydantic_settings"] = MagicMock()
sys.modules["pydantic_core"] = MagicMock()

# Now it's safe to import pytest and time
import pytest
import time

# --- Create specific mocks with proper behavior ---

# Redis mock with needed exceptions
redis_mock = sys.modules["redis"]
redis_mock.Redis = MagicMock()
redis_mock.ConnectionError = type("ConnectionError", (Exception,), {})
redis_mock.ResponseError = type("ResponseError", (Exception,), {})

# Logger mock
logger_mock = sys.modules["loguru"]
logger_mock.logger = MagicMock()

# Utils mock
utils_mock = sys.modules["src.mcp_suite.redis.utils"]
utils_mock.get_db_dir = MagicMock(return_value=Path("/tmp/redis-db"))

# Client mock
client_mock = sys.modules["src.mcp_suite.redis.client"]
client_mock.redis_client = MagicMock()
client_mock.connect_to_redis = MagicMock()

# --- Now load the real server module but ONLY the server module ---

# First save the existing mock
saved_server_mock = sys.modules["src.mcp_suite.redis.server"]

# Import the actual server module directly, bypassing normal imports
import importlib.util
spec = importlib.util.spec_from_file_location(
    "src.mcp_suite.redis.server",
    Path(__file__).parent.parent / "server.py"
)
server_module = importlib.util.module_from_spec(spec)

# Initialize global variables
server_module.redis_process = None
server_module.redis_launched_by_us = False

# Execute the module
spec.loader.exec_module(server_module)

# Replace the mock with the real module
sys.modules["src.mcp_suite.redis.server"] = server_module

# Grab the functions we need to test
parse_redis_url = server_module.parse_redis_url
launch_redis_server = server_module.launch_redis_server
shutdown_redis_server = server_module.shutdown_redis_server

# --- Pytest fixture to reset module globals and mocks ---
@pytest.fixture(autouse=True)
def restore_server_globals():
    # Save original values
    orig_process = getattr(server_module, "redis_process", None)
    orig_launched = getattr(server_module, "redis_launched_by_us", False)

    # Reset to known state
    server_module.redis_process = None
    server_module.redis_launched_by_us = False

    # Reset mocks
    redis_mock.Redis.reset_mock()
    logger_mock.logger.reset_mock()
    client_mock.redis_client.reset_mock()

    yield

    # Restore original values
    server_module.redis_process = orig_process
    server_module.redis_launched_by_us = orig_launched

# --- Test functions ---

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

def test_parse_redis_url_minimal():
    url = "redis://"
    host, port, password = parse_redis_url(url)
    assert host == "localhost"
    assert port == 6379
    assert password is None

def test_launch_redis_server_already_running():
    # Configure a mock instance that simulates a running Redis.
    mock_instance = MagicMock()
    mock_instance.ping.return_value = True
    redis_mock.Redis.return_value = mock_instance

    success, process = launch_redis_server()
    assert success is True
    assert process is None

    assert server_module.redis_launched_by_us is False

    redis_mock.Redis.assert_called_once()
    mock_instance.ping.assert_called_once()
    mock_instance.close.assert_called_once()

def test_launch_redis_server_new_instance():
    # Simulate that connecting to Redis initially fails.
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection refused")
    redis_mock.Redis.return_value = mock_instance

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # Process is running.

    with patch("subprocess.Popen", return_value=mock_proc):
        with patch("time.sleep"):  # Avoid delay in tests.
            success, process = launch_redis_server()
            assert success is True
            assert process == mock_proc

            assert server_module.redis_launched_by_us is True
            assert server_module.redis_process == mock_proc

def test_launch_redis_server_auth_error():
    # Simulate an authentication error from Redis.
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ResponseError("NOAUTH Authentication required")
    redis_mock.Redis.return_value = mock_instance

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("subprocess.Popen", return_value=mock_proc):
        with patch("time.sleep"):
            success, process = launch_redis_server()
            assert success is True
            assert process == mock_proc

            assert server_module.redis_launched_by_us is True
            assert server_module.redis_process == mock_proc

def test_launch_redis_server_failure():
    # Simulate failure to start Redis.
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection refused")
    redis_mock.Redis.return_value = mock_instance

    mock_proc = MagicMock()
    mock_proc.poll.return_value = 1  # Process indicates failure.
    mock_proc.communicate.return_value = ("", "Error starting Redis")

    with patch("subprocess.Popen", return_value=mock_proc):
        with patch("time.sleep"):
            success, process = launch_redis_server()
            assert success is False
            assert process is None

def test_launch_redis_server_exception():
    # Simulate an exception when launching Redis.
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection refused")
    redis_mock.Redis.return_value = mock_instance

    with patch("subprocess.Popen", side_effect=Exception("Failed to start Redis")):
        success, process = launch_redis_server()
        assert success is False
        assert process is None

        assert server_module.redis_launched_by_us is False

def test_launch_redis_server_socket_timeout():
    # Simulate a socket timeout scenario.
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection timed out")
    redis_mock.Redis.return_value = mock_instance

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("subprocess.Popen", return_value=mock_proc):
        with patch("time.sleep"):
            success, process = launch_redis_server()
            assert success is True
            assert process == mock_proc

            assert server_module.redis_launched_by_us is True
            assert server_module.redis_process == mock_proc

def test_shutdown_redis_server_not_launched_by_us():
    server_module.redis_launched_by_us = False
    server_module.redis_process = None

    shutdown_redis_server()
    client_mock.redis_client.shutdown.assert_not_called()

def test_shutdown_redis_server_launched_by_us():
    server_module.redis_launched_by_us = True
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # Process is running.
    server_module.redis_process = mock_proc

    shutdown_redis_server()
    client_mock.redis_client.shutdown.assert_called_once_with(save=True)
    mock_proc.terminate.assert_called_once()
    assert server_module.redis_launched_by_us is False
    assert server_module.redis_process is None


def test_shutdown_redis_server_force_kill():
    server_module.redis_launched_by_us = True
    mock_proc = MagicMock()
    # Simulate that terminate does not kill the process.
    mock_proc.poll.side_effect = [None, None, None]
    server_module.redis_process = mock_proc

    shutdown_redis_server()
    client_mock.redis_client.shutdown.assert_called_once_with(save=True)
    mock_proc.terminate.assert_called_once()
    mock_proc.kill.assert_called_once()
    assert server_module.redis_launched_by_us is False
    assert server_module.redis_process is None

def test_shutdown_redis_server_client_exception():
    """
    Test that if the Redis client shutdown call raises an exception,
    the exception is caught and logged as a warning, the process is terminated
    (with a forced kill if necessary), and the globals are reset.
    """
    server_module.redis_launched_by_us = True
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    server_module.redis_process = mock_proc
    client_mock.redis_client.shutdown.side_effect = Exception("Shutdown failed")
    with patch("src.mcp_suite.redis.server.logger", logger_mock.logger):
        shutdown_redis_server()
    client_mock.redis_client.shutdown.assert_called_once_with(save=True)
    mock_proc.terminate.assert_called_once()
    logger_mock.logger.warning.assert_any_call("Could not shutdown Redis via client: Shutdown failed")
    logger_mock.logger.warning.assert_any_call("Redis server not responding to terminate, forcing kill")
    logger_mock.logger.success.assert_called_with("Redis server shutdown complete")
    assert server_module.redis_launched_by_us is False
    assert server_module.redis_process is None

def test_shutdown_redis_server__terminate_fail_exception():
    """
    Test that if an exception occurs in the outer try block (e.g. if terminate() fails),
    it is caught and logged as an error, and the globals are reset.
    """
    server_module.redis_launched_by_us = True
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.terminate.side_effect = Exception("Terminate failed")
    server_module.redis_process = mock_proc
    client_mock.redis_client.shutdown.return_value = None
    with patch("src.mcp_suite.redis.server.logger", logger_mock.logger):
        shutdown_redis_server()
    client_mock.redis_client.shutdown.assert_called_once_with(save=True)
    mock_proc.terminate.assert_called_once()
    logger_mock.logger.error.assert_called_with("Error shutting down Redis server: Terminate failed")
    assert server_module.redis_launched_by_us is False
    assert server_module.redis_process is None

def test_launch_redis_server_with_custom_params():
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection refused")
    redis_mock.Redis.return_value = mock_instance

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
        with patch("time.sleep"):
            success, process = launch_redis_server(
                port=7000,
                password="custom_password",
                appendonly=False,
                keyspace_events="AKE"
            )
            assert success is True
            assert process == mock_proc

            call_args = mock_popen.call_args[0][0]
            assert "--port" in call_args
            assert "7000" in call_args
            assert "--requirepass" in call_args
            assert "custom_password" in call_args
            assert "--appendonly" not in call_args
            assert "--notify-keyspace-events" in call_args
            assert "AKE" in call_args
