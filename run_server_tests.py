#!/usr/bin/env python
"""
Run tests for Redis server module with 100% coverage.
This script bypasses the import issues by mocking dependencies.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import coverage

# Start coverage
cov = coverage.Coverage(source=["src.mcp_suite.redis.server"])
cov.start()

# Mock modules to avoid import errors
sys.modules["redis"] = MagicMock()
sys.modules["redis"].Redis = MagicMock()
sys.modules["redis"].ConnectionError = type("ConnectionError", (Exception,), {})
sys.modules["redis"].ResponseError = type("ResponseError", (Exception,), {})

sys.modules["loguru"] = MagicMock()
sys.modules["loguru"].logger = MagicMock()

# Mock environment
mock_env = MagicMock()
mock_env.REDIS = MagicMock()
mock_env.REDIS.URL = "redis://:testpassword@localhost:6379"
sys.modules["src.config.env"] = mock_env

# Mock utils
mock_utils = MagicMock()
mock_utils.get_db_dir = MagicMock(return_value=Path("/tmp/redis-db"))
sys.modules["src.mcp_suite.redis.utils"] = mock_utils

# Mock client
mock_client = MagicMock()
mock_client.redis_client = MagicMock()
sys.modules["src.mcp_suite.redis.client"] = mock_client

# Define global variables that will be used by the server module
redis_process = None
redis_launched_by_us = False

# Patch the global variables in the server module
import src.mcp_suite.redis.server

# Now we can safely import the server module
from src.mcp_suite.redis.server import (
    launch_redis_server,
    parse_redis_url,
    shutdown_redis_server,
)

src.mcp_suite.redis.server.redis_process = redis_process
src.mcp_suite.redis.server.redis_launched_by_us = redis_launched_by_us


class TestRedisServer(unittest.TestCase):
    """Test the Redis server module."""

    def setUp(self):
        """Reset state before each test."""
        # Reset global variables
        src.mcp_suite.redis.server.redis_process = None
        src.mcp_suite.redis.server.redis_launched_by_us = False

        # Reset mocks
        sys.modules["redis"].Redis.reset_mock()
        sys.modules["loguru"].logger.reset_mock()
        sys.modules["src.mcp_suite.redis.client"].redis_client.reset_mock()

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
        self.assertEqual(password, None)

    def test_parse_redis_url_minimal(self):
        """Test parsing a minimal Redis URL."""
        url = "redis://"
        host, port, password = parse_redis_url(url)
        self.assertEqual(host, "localhost")
        self.assertEqual(port, 6379)
        self.assertEqual(password, None)

    def test_launch_redis_server_already_running(self):
        """Test when Redis is already running."""
        # Configure mock
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        sys.modules["redis"].Redis.return_value = mock_instance

        # Call function
        success, process = launch_redis_server()

        # Assert
        self.assertTrue(success)
        self.assertIsNone(process)
        self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)

    def test_launch_redis_server_new_instance(self):
        """Test launching a new Redis instance."""
        # Configure mocks
        mock_instance = MagicMock()
        mock_instance.ping.side_effect = sys.modules["redis"].ConnectionError(
            "Connection refused"
        )
        sys.modules["redis"].Redis.return_value = mock_instance

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
        mock_instance.ping.side_effect = sys.modules["redis"].ResponseError(
            "NOAUTH Authentication required"
        )
        sys.modules["redis"].Redis.return_value = mock_instance

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
        mock_instance.ping.side_effect = sys.modules["redis"].ConnectionError(
            "Connection refused"
        )
        sys.modules["redis"].Redis.return_value = mock_instance

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
        mock_instance.ping.side_effect = sys.modules["redis"].ConnectionError(
            "Connection refused"
        )
        sys.modules["redis"].Redis.return_value = mock_instance

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
        mock_instance.ping.side_effect = sys.modules["redis"].ConnectionError(
            "Connection timed out"
        )
        sys.modules["redis"].Redis.return_value = mock_instance

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

    def test_launch_redis_server_custom_params(self):
        """Test launching Redis with custom parameters."""
        # Configure mocks
        mock_instance = MagicMock()
        mock_instance.ping.side_effect = sys.modules["redis"].ConnectionError(
            "Connection refused"
        )
        sys.modules["redis"].Redis.return_value = mock_instance

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Process running

        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            with patch("time.sleep"):  # Mock sleep to avoid waiting
                # Call function with custom parameters
                success, process = launch_redis_server(
                    port=1234,
                    password="custom_password",
                    appendonly=True,
                    keyspace_events="AKE",
                )

                # Assert
                self.assertTrue(success)
                self.assertEqual(process, mock_proc)

                # Verify command arguments
                call_args = mock_popen.call_args[0][0]
                self.assertIn("--port", call_args)
                self.assertIn("1234", call_args)
                self.assertIn("--requirepass", call_args)
                self.assertIn("custom_password", call_args)
                self.assertIn("--appendonly", call_args)
                self.assertIn("yes", call_args)
                self.assertIn("--notify-keyspace-events", call_args)
                self.assertIn("AKE", call_args)

    def test_launch_redis_server_no_appendonly(self):
        """Test launching Redis with appendonly disabled."""
        # Configure mocks
        mock_instance = MagicMock()
        mock_instance.ping.side_effect = sys.modules["redis"].ConnectionError(
            "Connection refused"
        )
        sys.modules["redis"].Redis.return_value = mock_instance

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Process running

        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            with patch("time.sleep"):  # Mock sleep to avoid waiting
                # Call function with appendonly=False
                success, process = launch_redis_server(appendonly=False)

                # Assert
                self.assertTrue(success)
                self.assertEqual(process, mock_proc)

                # Verify command arguments
                call_args = mock_popen.call_args[0][0]
                self.assertNotIn("--appendonly", call_args)

    def test_shutdown_redis_server(self):
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
        self.assertIsNone(src.mcp_suite.redis.server.redis_process)
        self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)

    def test_shutdown_redis_server_with_client(self):
        """Test shutting down Redis with client."""
        # Set up test state
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Process is running
        src.mcp_suite.redis.server.redis_process = mock_proc
        src.mcp_suite.redis.server.redis_launched_by_us = True

        # Call function
        shutdown_redis_server()

        # Assert
        sys.modules[
            "src.mcp_suite.redis.client"
        ].redis_client.shutdown.assert_called_once_with(save=True)
        self.assertIsNone(src.mcp_suite.redis.server.redis_process)
        self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)

    def test_shutdown_redis_server_client_exception(self):
        """Test client exception during shutdown."""
        # Set up test state
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Process is running
        src.mcp_suite.redis.server.redis_process = mock_proc
        src.mcp_suite.redis.server.redis_launched_by_us = True

        # Set up client mock with exception
        sys.modules["src.mcp_suite.redis.client"].redis_client.shutdown.side_effect = (
            Exception("Shutdown failed")
        )

        # Call function
        shutdown_redis_server()

        # Assert
        mock_proc.terminate.assert_called_once()
        self.assertIsNone(src.mcp_suite.redis.server.redis_process)
        self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)

    def test_shutdown_redis_server_force_kill(self):
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
            mock_proc.terminate.assert_called_once()
            mock_proc.kill.assert_called_once()
            self.assertIsNone(src.mcp_suite.redis.server.redis_process)
            self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)

    def test_shutdown_redis_server_not_launched_by_us(self):
        """Test shutdown when Redis wasn't launched by us."""
        # Set up test state
        mock_proc = MagicMock()
        src.mcp_suite.redis.server.redis_process = mock_proc
        src.mcp_suite.redis.server.redis_launched_by_us = False

        # Call function
        shutdown_redis_server()

        # Assert
        mock_proc.terminate.assert_not_called()
        self.assertEqual(
            src.mcp_suite.redis.server.redis_process, mock_proc
        )  # Should not change
        self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)

    def test_shutdown_redis_server_already_terminated(self):
        """Test shutdown when Redis has already terminated."""
        # Set up test state - process is None but launched flag is True
        src.mcp_suite.redis.server.redis_process = None
        src.mcp_suite.redis.server.redis_launched_by_us = True

        # Mock the redis_client to avoid issues
        mock_client = MagicMock()
        with patch("src.mcp_suite.redis.client.redis_client", mock_client):
            # Call function
            shutdown_redis_server()

            # Assert - In this case, the flag should remain True because the condition
            # "redis_launched_by_us and redis_process is not None" is not satisfied
            self.assertTrue(src.mcp_suite.redis.server.redis_launched_by_us)

    def test_shutdown_redis_server_exception_during_termination(self):
        """Test exception during Redis termination."""
        # Set up test state
        mock_proc = MagicMock()
        mock_proc.terminate.side_effect = Exception("Failed to terminate")
        src.mcp_suite.redis.server.redis_process = mock_proc
        src.mcp_suite.redis.server.redis_launched_by_us = True

        # Call function
        shutdown_redis_server()

        # Assert
        self.assertIsNone(src.mcp_suite.redis.server.redis_process)
        self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)

    def test_shutdown_redis_server_with_force_kill_exception(self):
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
            mock_proc.terminate.assert_called_once()
            mock_proc.kill.assert_called_once()
            self.assertIsNone(src.mcp_suite.redis.server.redis_process)
            self.assertFalse(src.mcp_suite.redis.server.redis_launched_by_us)


if __name__ == "__main__":
    # Run the tests
    unittest.main(argv=["first-arg-is-ignored"], exit=False)

    # Report coverage
    cov.stop()
    cov.save()
    print("\nCoverage Report:")
    cov.report(show_missing=True)
