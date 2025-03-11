"""Tests for Redis server module."""

# Important: We need to patch modules BEFORE they are imported
import sys
from unittest.mock import MagicMock, patch

# Create mock for redis module
redis_mock = MagicMock()
redis_mock.Redis = MagicMock()
redis_mock.ConnectionError = type("ConnectionError", (Exception,), {})
redis_mock.ResponseError = type("ResponseError", (Exception,), {})
sys.modules["redis"] = redis_mock

# Create mock for loguru module
logger_mock = MagicMock()
logger_mock.logger = MagicMock()
sys.modules["loguru"] = logger_mock

# Create a proper mock for pydantic_settings
pydantic_settings_mock = MagicMock()
BaseSettings_mock = MagicMock()
ConfigDict_mock = MagicMock()
pydantic_settings_mock.BaseSettings = BaseSettings_mock
sys.modules["pydantic_settings"] = pydantic_settings_mock

# Create a proper mock for pydantic
pydantic_mock = MagicMock()
pydantic_mock.ConfigDict = ConfigDict_mock
sys.modules["pydantic"] = pydantic_mock

# Create a proper LLM class mock
class MockLLM:
    OPENAI_API_KEY = "mock_openai_key"
    ANTHROPIC_API_KEY = "mock_anthropic_key"
    GEMINI_API_KEY = "mock_gemini_key"

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True, "extra": "allow", "env_prefix": "LLM_"}

# Create environment mock
env_mock = MagicMock()
env_mock.REDIS = MagicMock()
env_mock.REDIS.URL = "redis://:testpassword@localhost:6379"
env_mock.REDDIT = MagicMock()
env_mock.REDDIT.CLIENT_ID = "mock_client_id"
env_mock.REDDIT.CLIENT_SECRET = "mock_client_secret"
env_mock.REDDIT.USER_AGENT = "mock_user_agent"
env_mock.MODELS = MagicMock()
env_mock.LLMS = MagicMock()
env_mock.OPENAI = MagicMock()
env_mock.ANTHROPIC = MagicMock()
env_mock.AZURE = MagicMock()
env_mock.COHERE = MagicMock()
env_mock.LLM = MockLLM
env_mock.LLM_API_KEYS = MockLLM()
sys.modules["src.config.env"] = env_mock

from pathlib import Path
from unittest.mock import patch

# Now import other modules
import pytest

# Mock utils
utils_mock = MagicMock()
utils_mock.get_db_dir = MagicMock(return_value=Path("/tmp/redis-db"))
sys.modules["src.mcp_suite.redis.utils"] = utils_mock

# Mock client
client_mock = MagicMock()
client_mock.redis_client = MagicMock()
sys.modules["src.mcp_suite.redis.client"] = client_mock

# Get direct reference to server module to modify globals
import src.mcp_suite.redis.server

# Import the server module functions AFTER mocking dependencies
from src.mcp_suite.redis.server import (
    launch_redis_server,
    parse_redis_url,
    shutdown_redis_server,
)


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global variables before each test."""
    # Store original values
    orig_process = src.mcp_suite.redis.server.redis_process
    orig_launched = src.mcp_suite.redis.server.redis_launched_by_us

    # Reset globals
    src.mcp_suite.redis.server.redis_process = None
    src.mcp_suite.redis.server.redis_launched_by_us = False

    # Reset mocks
    redis_mock.Redis.reset_mock()
    logger_mock.logger.reset_mock()
    client_mock.redis_client.reset_mock()

    yield

    # Restore original values after test
    src.mcp_suite.redis.server.redis_process = orig_process
    src.mcp_suite.redis.server.redis_launched_by_us = orig_launched


def test_parse_redis_url():
    """Test parsing a Redis URL with all components."""
    url = "redis://:mypassword@127.0.0.1:6380"
    host, port, password = parse_redis_url(url)
    assert host == "127.0.0.1"
    assert port == 6380
    assert password == "mypassword"


def test_parse_redis_url_defaults():
    """Test parsing a Redis URL with defaults."""
    url = "redis://localhost"
    host, port, password = parse_redis_url(url)
    assert host == "localhost"
    assert port == 6379
    assert password is None


def test_parse_redis_url_minimal():
    """Test parsing a minimal Redis URL."""
    url = "redis://"
    host, port, password = parse_redis_url(url)
    assert host == "localhost"
    assert port == 6379
    assert password is None


def test_launch_redis_server_already_running():
    """Test when Redis is already running."""
    # Configure mock
    mock_instance = MagicMock()
    mock_instance.ping.return_value = True
    redis_mock.Redis.return_value = mock_instance

    # Call function
    success, process = launch_redis_server()

    # Assert
    assert success is True
    assert process is None
    assert src.mcp_suite.redis.server.redis_launched_by_us is False
    redis_mock.Redis.assert_called_once()
    mock_instance.ping.assert_called_once()
    mock_instance.close.assert_called_once()


def test_launch_redis_server_new_instance():
    """Test launching a new Redis instance."""
    # Configure mocks
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection refused")
    redis_mock.Redis.return_value = mock_instance

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # Process running

    with patch("subprocess.Popen", return_value=mock_proc):
        with patch("time.sleep"):  # Mock sleep to avoid waiting
            # Call function
            success, process = launch_redis_server()

            # Assert
            assert success is True
            assert process is mock_proc
            assert src.mcp_suite.redis.server.redis_launched_by_us is True
            assert src.mcp_suite.redis.server.redis_process is mock_proc


def test_launch_redis_server_auth_error():
    """Test when Redis connection fails with auth error."""
    # Configure mocks
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ResponseError("NOAUTH Authentication required")
    redis_mock.Redis.return_value = mock_instance

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # Process running

    with patch("subprocess.Popen", return_value=mock_proc):
        with patch("time.sleep"):  # Mock sleep to avoid waiting
            # Call function
            success, process = launch_redis_server()

            # Assert
            assert success is True
            assert process is mock_proc
            assert src.mcp_suite.redis.server.redis_launched_by_us is True
            assert src.mcp_suite.redis.server.redis_process is mock_proc


def test_launch_redis_server_failure():
    """Test when Redis server fails to start."""
    # Configure mocks
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection refused")
    redis_mock.Redis.return_value = mock_instance

    mock_proc = MagicMock()
    mock_proc.poll.return_value = 1  # Process failed
    mock_proc.communicate.return_value = ("", "Error starting Redis")

    with patch("subprocess.Popen", return_value=mock_proc):
        with patch("time.sleep"):  # Mock sleep to avoid waiting
            # Call function
            success, process = launch_redis_server()

            # Assert
            assert success is False
            assert process is None
            assert src.mcp_suite.redis.server.redis_launched_by_us is False
            assert src.mcp_suite.redis.server.redis_process is None


def test_launch_redis_server_exception():
    """Test when an exception occurs during launch."""
    # Configure mocks
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection refused")
    redis_mock.Redis.return_value = mock_instance

    with patch("subprocess.Popen", side_effect=Exception("Failed to start Redis")):
        # Call function
        success, process = launch_redis_server()

        # Assert
        assert success is False
        assert process is None
        assert src.mcp_suite.redis.server.redis_launched_by_us is False


def test_launch_redis_server_socket_timeout():
    """Test when Redis connection times out."""
    # Configure mocks
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection timed out")
    redis_mock.Redis.return_value = mock_instance

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # Process running

    with patch("subprocess.Popen", return_value=mock_proc):
        with patch("time.sleep"):  # Mock sleep to avoid waiting
            # Call function
            success, process = launch_redis_server()

            # Assert
            assert success is True
            assert process is mock_proc
            assert src.mcp_suite.redis.server.redis_launched_by_us is True
            assert src.mcp_suite.redis.server.redis_process is mock_proc


def test_launch_redis_server_custom_params():
    """Test launching Redis with custom parameters."""
    # Configure mocks
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection refused")
    redis_mock.Redis.return_value = mock_instance

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # Process running

    with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
        with patch("time.sleep"):  # Mock sleep to avoid waiting
            # Call function with custom parameters
            success, process = launch_redis_server(
                port=7000,
                password="custom_password",
                appendonly=False,
                keyspace_events="AKE"
            )

            # Assert
            assert success is True
            assert process is mock_proc

            # Check that Popen was called with the right arguments
            call_args = mock_popen.call_args[0][0]
            assert "--port" in call_args
            assert "7000" in call_args
            assert "--requirepass" in call_args
            assert "custom_password" in call_args
            assert "--appendonly" not in call_args or call_args[call_args.index("--appendonly") + 1] != "yes"
            assert "--notify-keyspace-events" in call_args
            assert "AKE" in call_args


def test_launch_redis_server_no_appendonly():
    """Test launching Redis with appendonly disabled."""
    # Configure mocks
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection refused")
    redis_mock.Redis.return_value = mock_instance

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # Process running

    with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
        with patch("time.sleep"):  # Mock sleep to avoid waiting
            # Call function with appendonly=False
            success, process = launch_redis_server(appendonly=False)

            # Assert
            assert success is True
            assert process is mock_proc

            # Verify command arguments
            call_args = mock_popen.call_args[0][0]
            assert "--appendonly" not in call_args


def test_shutdown_redis_server():
    """Test shutting down Redis server."""
    # Set up test state
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # Process is running
    src.mcp_suite.redis.server.redis_process = mock_proc
    src.mcp_suite.redis.server.redis_launched_by_us = True

    # Call function
    shutdown_redis_server()

    # Assert
    mock_proc.terminate.assert_called_once()
    assert src.mcp_suite.redis.server.redis_process is None
    assert src.mcp_suite.redis.server.redis_launched_by_us is False


def test_shutdown_redis_server_with_client():
    """Test shutting down Redis with client."""
    # Set up test state
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # Process is running
    src.mcp_suite.redis.server.redis_process = mock_proc
    src.mcp_suite.redis.server.redis_launched_by_us = True

    # Call function
    shutdown_redis_server()

    # Assert
    client_mock.redis_client.shutdown.assert_called_once_with(save=True)
    assert src.mcp_suite.redis.server.redis_process is None
    assert src.mcp_suite.redis.server.redis_launched_by_us is False


def test_shutdown_redis_server_client_exception():
    """Test client exception during shutdown."""
    # Set up test state
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # Process is running
    src.mcp_suite.redis.server.redis_process = mock_proc
    src.mcp_suite.redis.server.redis_launched_by_us = True

    # Set up client mock with exception
    client_mock.redis_client.shutdown.side_effect = (
        Exception("Shutdown failed")
    )

    # Call function
    shutdown_redis_server()

    # Assert
    client_mock.redis_client.shutdown.assert_called_once_with(save=True)
    mock_proc.terminate.assert_called_once()
    assert src.mcp_suite.redis.server.redis_process is None
    assert src.mcp_suite.redis.server.redis_launched_by_us is False


def test_shutdown_redis_server_force_kill():
    """Test force kill during Redis shutdown."""
    # Set up test state
    mock_proc = MagicMock()
    mock_proc.poll.side_effect = [None, None]  # Still running after terminate
    src.mcp_suite.redis.server.redis_process = mock_proc
    src.mcp_suite.redis.server.redis_launched_by_us = True

    with patch("time.sleep"):  # Mock sleep to avoid waiting
        # Call function
        shutdown_redis_server()

        # Assert
        client_mock.redis_client.shutdown.assert_called_once_with(save=True)
        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()
        assert src.mcp_suite.redis.server.redis_process is None
        assert src.mcp_suite.redis.server.redis_launched_by_us is False


def test_shutdown_redis_server_with_force_kill_exception():
    """Test when force kill raises an exception."""
    # Set up test state
    mock_proc = MagicMock()
    mock_proc.poll.side_effect = [None, None]  # Still running after terminate
    mock_proc.kill.side_effect = Exception("Failed to kill")
    src.mcp_suite.redis.server.redis_process = mock_proc
    src.mcp_suite.redis.server.redis_launched_by_us = True

    with patch("time.sleep"):  # Mock sleep to avoid waiting
        # Call function
        shutdown_redis_server()

        # Assert
        client_mock.redis_client.shutdown.assert_called_once_with(save=True)
        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()
        assert src.mcp_suite.redis.server.redis_process is None
        assert src.mcp_suite.redis.server.redis_launched_by_us is False


def test_shutdown_redis_server_not_launched_by_us():
    """Test shutdown when Redis wasn't launched by us."""
    # Set up test state
    mock_proc = MagicMock()
    src.mcp_suite.redis.server.redis_process = mock_proc
    src.mcp_suite.redis.server.redis_launched_by_us = False

    # Call function
    shutdown_redis_server()

    # Assert
    client_mock.redis_client.shutdown.assert_not_called()
    assert src.mcp_suite.redis.server.redis_process is mock_proc  # Should not change
    assert src.mcp_suite.redis.server.redis_launched_by_us is False


def test_shutdown_redis_server_already_terminated():
    """Test shutdown when Redis has already terminated."""
    # Set up test state - process is None but launched flag is True
    src.mcp_suite.redis.server.redis_process = None
    src.mcp_suite.redis.server.redis_launched_by_us = True

    # Call function
    shutdown_redis_server()

    # Assert - flag should remain True per server.py implementation
    assert src.mcp_suite.redis.server.redis_launched_by_us is True


def test_shutdown_redis_server_exception_during_termination():
    """Test exception during Redis termination."""
    # Set up test state
    mock_proc = MagicMock()
    mock_proc.terminate.side_effect = Exception("Failed to terminate")
    src.mcp_suite.redis.server.redis_process = mock_proc
    src.mcp_suite.redis.server.redis_launched_by_us = True

    # Call function
    shutdown_redis_server()

    # Assert
    client_mock.redis_client.shutdown.assert_called_once_with(save=True)
    mock_proc.terminate.assert_called_once()
    assert src.mcp_suite.redis.server.redis_process is None
    assert src.mcp_suite.redis.server.redis_launched_by_us is False
