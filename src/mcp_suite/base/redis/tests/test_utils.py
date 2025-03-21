"""Tests for the Redis utilities module."""

from pathlib import Path
from unittest.mock import call, patch

import pytest
from loguru import logger

from mcp_suite.base.redis import utils


@pytest.fixture
def reset_utils_state():
    """Reset the global state in utils module between tests."""
    # Save original values
    original_logger_ids = utils.logger_ids.copy()
    original_logger_configured = utils.logger_configured
    original_logs_dir = utils.logs_dir
    original_db_dir = utils.db_dir

    # Reset for test
    utils.logger_ids = []
    utils.logger_configured = False

    yield

    # Restore original values after test
    utils.logger_ids = original_logger_ids
    utils.logger_configured = original_logger_configured
    utils.logs_dir = original_logs_dir
    utils.db_dir = original_db_dir


class TestSetupDirectories:
    """Tests for the setup_directories function."""

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.mkdir")
    @patch("mcp_suite.base.redis.utils.logger")
    def test_creates_directories_when_not_exist(
        self, mock_logger, mock_mkdir, mock_exists
    ):
        """Test that directories are created when they don't exist."""
        # Setup
        mock_exists.return_value = False

        # Execute
        utils.setup_directories()

        # Assert
        assert mock_mkdir.call_count == 2
        mock_mkdir.assert_has_calls(
            [call(parents=True, exist_ok=True), call(parents=True, exist_ok=True)]
        )
        # Verify logger.info was called for each directory creation
        assert mock_logger.info.call_count == 2
        mock_logger.info.assert_any_call(f"Created logs directory at {utils.logs_dir}")
        mock_logger.info.assert_any_call(
            f"Created Redis database directory at {utils.db_dir}"
        )

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.mkdir")
    @patch("mcp_suite.base.redis.utils.logger")
    def test_skips_directory_creation_when_exist(
        self, mock_logger, mock_mkdir, mock_exists
    ):
        """Test that directories are not created when they already exist."""
        # Setup
        mock_exists.return_value = True

        # Execute
        utils.setup_directories()

        # Assert
        mock_mkdir.assert_not_called()
        # No logger calls should be made for existing directories
        mock_logger.info.assert_not_called()

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.home")
    @patch("mcp_suite.base.redis.utils.logger")
    def test_fallback_on_permission_error_logs(
        self, mock_logger, mock_home, mock_mkdir, mock_exists
    ):
        """Test fallback to home directory when permission error occurs for logs."""
        # Setup
        mock_exists.return_value = False
        mock_home.return_value = Path("/mock/home")

        # Make first mkdir call raise PermissionError, second call succeed
        mock_mkdir.side_effect = [PermissionError, None, None, None]

        # Execute
        utils.setup_directories()

        # Assert
        assert mock_mkdir.call_count >= 2
        assert utils.logs_dir == Path("/mock/home/logs")

        # Verify warning log was called for logs directory fallback
        mock_logger.warning.assert_any_call(
            f"Using fallback logs directory at {utils.logs_dir} due to permission error"
        )

        # Verify info log was called for db directory creation
        mock_logger.info.assert_called_once_with(
            f"Created Redis database directory at {utils.db_dir}"
        )

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.home")
    @patch("mcp_suite.base.redis.utils.logger")
    def test_fallback_on_permission_error_db(
        self, mock_logger, mock_home, mock_mkdir, mock_exists
    ):
        """Test fallback to home directory when permission error occurs for db."""
        # Setup
        mock_exists.return_value = False
        mock_home.return_value = Path("/mock/home")

        # Make second mkdir call raise PermissionError
        mock_mkdir.side_effect = [None, PermissionError, None]

        # Execute
        utils.setup_directories()

        # Assert
        assert mock_mkdir.call_count >= 3
        assert utils.db_dir == Path("/mock/home/db")

        # Verify info log was called for logs directory creation
        mock_logger.info.assert_called_once_with(
            f"Created logs directory at {utils.logs_dir}"
        )

        # Verify warning log was called for db directory fallback
        mock_logger.warning.assert_called_once_with(
            f"Using fallback Redis database directory at {utils.db_dir} "
            f"due to permission error"
        )

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.home")
    @patch("mcp_suite.base.redis.utils.logger")
    def test_both_permission_errors(
        self, mock_logger, mock_home, mock_mkdir, mock_exists
    ):
        """Test when permission errors occur for both logs and db directories."""
        # Setup
        mock_exists.return_value = False
        mock_home.return_value = Path("/mock/home")

        # Make both mkdir calls raise PermissionError for original directories
        mock_mkdir.side_effect = [PermissionError, None, PermissionError, None]

        # Execute
        utils.setup_directories()

        # Assert
        assert mock_mkdir.call_count >= 4
        assert utils.logs_dir == Path("/mock/home/logs")
        assert utils.db_dir == Path("/mock/home/db")

        # Verify both warning logs were called
        assert mock_logger.warning.call_count == 2
        mock_logger.warning.assert_any_call(
            f"Using fallback logs directory at {utils.logs_dir} due to permission error"
        )
        mock_logger.warning.assert_any_call(
            f"Using fallback Redis database directory at {utils.db_dir} "
            f"due to permission error"
        )


class TestConfigureLogger:
    """Tests for the configure_logger function."""

    @pytest.fixture
    def reset_logger(self):
        """Reset logger state after test."""
        yield
        utils.logger_configured = False
        utils.logger_ids = []
        logger.remove()

    @patch("loguru.logger.add")
    @patch("loguru.logger.remove")
    def test_configure_logger_first_time(
        self, mock_remove, mock_add, reset_utils_state, reset_logger
    ):
        """Test logger configuration when it hasn't been configured yet."""
        # Setup
        mock_add.side_effect = ["stderr_id", "file_id"]

        # Execute
        utils.configure_logger()

        # Assert
        mock_remove.assert_called_once()
        assert mock_add.call_count == 2
        assert utils.logger_configured is True
        assert len(utils.logger_ids) == 2
        assert "stderr_id" in utils.logger_ids
        assert "file_id" in utils.logger_ids

    @patch("loguru.logger.add")
    @patch("loguru.logger.remove")
    def test_configure_logger_already_configured(
        self, mock_remove, mock_add, reset_utils_state, reset_logger
    ):
        """Test logger configuration when it's already been configured."""
        # Setup
        utils.logger_configured = True

        # Execute
        utils.configure_logger()

        # Assert
        mock_remove.assert_not_called()
        mock_add.assert_not_called()

    @patch("loguru.logger.add")
    @patch("loguru.logger.remove")
    def test_configure_logger_handles_existing_ids(self, mock_remove, mock_add):
        """Test that existing logger IDs are properly removed."""
        # Setup - save original values
        original_logger_ids = utils.logger_ids.copy()
        original_logger_configured = utils.logger_configured

        # Set test values
        utils.logger_ids = ["old_id1", "old_id2"]
        utils.logger_configured = False

        # Configure mocks
        # Use a list with enough values to avoid StopIteration
        mock_remove.side_effect = [None, None, ValueError, None, None, None]
        mock_add.side_effect = ["new_stderr_id", "new_file_id"]

        try:
            # Execute
            utils.configure_logger()

            # Assert
            assert (
                mock_remove.call_count >= 3
            )  # Initial remove() + 2 specific ID removals
            assert mock_add.call_count == 2
            assert utils.logger_ids == ["new_stderr_id", "new_file_id"]
        finally:
            # Restore original values
            utils.logger_ids = original_logger_ids
            utils.logger_configured = original_logger_configured
            # Don't call logger.remove() directly as it's mocked
            mock_remove.side_effect = None  # Reset side_effect to avoid StopIteration

    @patch("loguru.logger.add")
    @patch("loguru.logger.remove")
    @patch("loguru.logger.warning")
    def test_configure_logger_handles_file_exception(
        self, mock_warning, mock_remove, mock_add, reset_utils_state, reset_logger
    ):
        """Test that exceptions during file logger setup are handled gracefully."""
        # Setup
        mock_add.side_effect = ["stderr_id", Exception("File error")]

        # Execute
        utils.configure_logger()

        # Assert
        assert mock_add.call_count == 2
        mock_warning.assert_called_once()
        assert utils.logger_configured is True
        assert utils.logger_ids == ["stderr_id"]


class TestCleanupLogger:
    """Tests for the cleanup_logger function."""

    @patch("loguru.logger.remove")
    def test_cleanup_logger(self, mock_remove, reset_utils_state):
        """Test that logger is properly cleaned up."""
        # Setup
        utils.logger_ids = ["id1", "id2"]
        utils.logger_configured = True

        # Execute
        utils.cleanup_logger()

        # Assert
        mock_remove.assert_called_once()
        assert utils.logger_ids == []
        assert utils.logger_configured is False


class TestGetDbDir:
    """Tests for the get_db_dir function."""

    def test_get_db_dir(self):
        """Test that get_db_dir returns the correct directory."""
        # Execute
        result = utils.get_db_dir()

        # Assert
        assert result == utils.db_dir
        assert isinstance(result, Path)
