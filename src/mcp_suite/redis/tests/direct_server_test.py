"""Direct tests for Redis server module without importing the module directly."""

import os
import sys
import unittest
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
pydantic_settings_mock.BaseSettings = BaseSettings_mock
sys.modules["pydantic_settings"] = pydantic_settings_mock

# Create a proper mock for pydantic
pydantic_mock = MagicMock()
ConfigDict_mock = MagicMock()
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
env_mock.LLM = MockLLM
env_mock.LLM_API_KEYS = MockLLM()
sys.modules["src.config.env"] = env_mock

# Mock utils module
from pathlib import Path
utils_mock = MagicMock()
utils_mock.get_db_dir = MagicMock(return_value=Path("/tmp/redis-db"))
sys.modules["src.mcp_suite.redis.utils"] = utils_mock

# Create a mock for the client module
client_mock = MagicMock()
client_mock.redis_client = MagicMock()
sys.modules["src.mcp_suite.redis.client"] = client_mock

# Define global variables that will be patched in the server module
redis_process_global = None
redis_launched_by_us_global = False

# Create a mock server module
server_mock = MagicMock()
server_mock.redis_process = redis_process_global
server_mock.redis_launched_by_us = redis_launched_by_us_global
sys.modules["src.mcp_suite.redis.server"] = server_mock

# Now import the actual server module code
from src.mcp_suite.redis.server import parse_redis_url, launch_redis_server, shutdown_redis_server

# Get direct reference to server module to modify globals
import src.mcp_suite.redis.server


class TestRedisServer(unittest.TestCase):
    """Test Redis server functions."""

    def setUp(self):
        """Set up test environment."""
        # Store original values
        self.orig_process = src.mcp_suite.redis.server.redis_process
        self.orig_launched = src.mcp_suite.redis.server.redis_launched_by_us

        # Reset globals
        src.mcp_suite.redis.server.redis_process = None
        src.mcp_suite.redis.server.redis_launched_by_us = False

        # Reset mocks
        redis_mock.Redis.reset_mock()
        logger_mock.logger.reset_mock()
        client_mock.redis_client.reset_mock()

    def tearDown(self):
        """Tear down test environment."""
        # Restore original values
        src.mcp_suite.redis.server.redis_process = self.orig_process
        src.mcp_suite.redis.server.redis_launched_by_us = self.orig_launched

    def test_parse_redis_url(self):
        """Test parsing a Redis URL with all components."""
        url = "redis://:mypassword@127.0.0.1:6380"
        host, port, password = parse_redis_url(url)
        self.assertEqual(host, "127.0.0.1")
        self.assertEqual(port, 6380)
        self.assertEqual(password, "mypassword")

    def test_parse_redis_url_defaults(self):
        """Test parsing a Redis URL with defaults."""
        url = "redis://localhost"
        host, port, password = parse_redis_url(url)
        self.assertEqual(host, "localhost")
        self.assertEqual(port, 6379)
        self.assertIsNone(password)

    def test_parse_redis_url_minimal(self):
        """Test parsing a minimal Redis URL."""
        url = "redis://"
        host, port, password = parse_redis_url(url)
        self.assertEqual(host, "localhost")
        self.assertEqual(port, 6379)
        self.assertIsNone(password)

    def test_launch_redis_server_already_running(self):
        """Test when Redis is already running."""
        # Configure mock
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        redis_mock.Redis.return_value = mock_instance

        # Call function
        success, process = launch_redis_server()

        # Assert
        self.assertTrue(success)
        self.assertIsNone(process)
        self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)
        redis_mock.Redis.assert_called_once()
        mock_instance.ping.assert_called_once()
        mock_instance.close.assert_called_once()

    def test_launch_redis_server_new_instance(self):
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
                self.assertTrue(success)
                self.assertEqual(process, mock_proc)
                self.assertTrue(src.mcp_suite.redis.server.redis_launched_by_us)
                self.assertEqual(src.mcp_suite.redis.server.redis_process, mock_proc)

    def test_launch_redis_server_auth_error(self):
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
                self.assertTrue(success)
                self.assertEqual(process, mock_proc)
                self.assertTrue(src.mcp_suite.redis.server.redis_launched_by_us)
                self.assertEqual(src.mcp_suite.redis.server.redis_process, mock_proc)

    def test_launch_redis_server_failure(self):
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
                self.assertFalse(success)
                self.assertIsNone(process)
                self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)
                self.assertIsNone(src.mcp_suite.redis.server.redis_process)

    def test_launch_redis_server_exception(self):
        """Test when an exception occurs during launch."""
        # Configure mocks
        mock_instance = MagicMock()
        mock_instance.ping.side_effect = redis_mock.ConnectionError("Connection refused")
        redis_mock.Redis.return_value = mock_instance

        with patch("subprocess.Popen", side_effect=Exception("Failed to start Redis")):
            # Call function
            success, process = launch_redis_server()

            # Assert
            self.assertFalse(success)
            self.assertIsNone(process)
            self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)

    def test_launch_redis_server_socket_timeout(self):
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
                self.assertTrue(success)
                self.assertEqual(process, mock_proc)
                self.assertTrue(src.mcp_suite.redis.server.redis_launched_by_us)
                self.assertEqual(src.mcp_suite.redis.server.redis_process, mock_proc)

    def test_shutdown_redis_server_not_launched_by_us(self):
        """Test shutdown when Redis was not launched by us."""
        # Set up the test condition
        src.mcp_suite.redis.server.redis_launched_by_us = False
        src.mcp_suite.redis.server.redis_process = None

        # Call function
        shutdown_redis_server()

        # Assert
        client_mock.redis_client.shutdown.assert_not_called()

    def test_shutdown_redis_server_launched_by_us(self):
        """Test shutdown when Redis was launched by us."""
        # Set up the test condition
        src.mcp_suite.redis.server.redis_launched_by_us = True
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Process is running
        src.mcp_suite.redis.server.redis_process = mock_proc

        # Call function
        shutdown_redis_server()

        # Assert
        client_mock.redis_client.shutdown.assert_called_once_with(save=True)
        mock_proc.terminate.assert_called_once()
        self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)
        self.assertIsNone(src.mcp_suite.redis.server.redis_process)

    def test_shutdown_redis_server_client_exception(self):
        """Test shutdown when client shutdown raises an exception."""
        # Set up the test condition
        src.mcp_suite.redis.server.redis_launched_by_us = True
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Process is running
        src.mcp_suite.redis.server.redis_process = mock_proc
        client_mock.redis_client.shutdown.side_effect = Exception("Shutdown failed")

        # Call function
        shutdown_redis_server()

        # Assert
        client_mock.redis_client.shutdown.assert_called_once_with(save=True)
        mock_proc.terminate.assert_called_once()
        self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)
        self.assertIsNone(src.mcp_suite.redis.server.redis_process)

    def test_shutdown_redis_server_force_kill(self):
        """Test shutdown when terminate doesn't work and force kill is needed."""
        # Set up the test condition
        src.mcp_suite.redis.server.redis_launched_by_us = True
        mock_proc = MagicMock()
        # Process still running after terminate
        mock_proc.poll.side_effect = [None, None, None]
        src.mcp_suite.redis.server.redis_process = mock_proc

        # Call function
        shutdown_redis_server()

        # Assert
        client_mock.redis_client.shutdown.assert_called_once_with(save=True)
        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()
        self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)
        self.assertIsNone(src.mcp_suite.redis.server.redis_process)

    def test_shutdown_redis_server_exception(self):
        """Test shutdown when an exception occurs."""
        # Set up the test condition
        src.mcp_suite.redis.server.redis_launched_by_us = True
        mock_proc = MagicMock()
        mock_proc.terminate.side_effect = Exception("Termination failed")
        src.mcp_suite.redis.server.redis_process = mock_proc

        # Call function
        shutdown_redis_server()

        # Assert
        client_mock.redis_client.shutdown.assert_called_once_with(save=True)
        mock_proc.terminate.assert_called_once()
        self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)
        self.assertIsNone(src.mcp_suite.redis.server.redis_process)

    def test_launch_redis_server_with_custom_params(self):
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
                self.assertTrue(success)
                self.assertEqual(process, mock_proc)

                # Check that Popen was called with the right arguments
                call_args = mock_popen.call_args[0][0]
                self.assertIn("--port", call_args)
                self.assertIn("7000", call_args)
                self.assertIn("--requirepass", call_args)
                self.assertIn("custom_password", call_args)
                self.assertNotIn("--appendonly", call_args)
                self.assertIn("--notify-keyspace-events", call_args)
                self.assertIn("AKE", call_args)


if __name__ == "__main__":
    # Run the tests with coverage
    import coverage

    cov = coverage.Coverage(source=["src.mcp_suite.redis.server"])
    cov.start()

    # Run the tests
    unittest.main(exit=False)

    # Stop coverage and report
    cov.stop()
    cov.save()

    print("\nCoverage Report:")
    cov.report()