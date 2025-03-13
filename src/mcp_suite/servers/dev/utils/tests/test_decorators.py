"""Tests for the decorators module.

This module contains tests for the utility decorators in the dev server,
particularly focusing on the exception_handler decorator which provides
self-repair capabilities to MCP tool functions.
"""

import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest

from mcp_suite.servers.dev.utils.decorators import exception_handler


class TestExceptionHandler:
    """Tests for the exception_handler decorator."""

    def test_sync_function_no_exception(self):
        """Test that a sync function with no exceptions works normally."""

        # Define a simple function that doesn't raise exceptions
        @exception_handler()
        def sample_function(x, y):
            return x + y

        # Call the function and check the result
        result = sample_function(2, 3)
        assert result == 5

    def test_sync_function_with_handled_exception(self):
        """Test that a sync function with a handled exception returns the expected
        error structure."""

        # Define a function that raises a ValueError
        @exception_handler()
        def sample_function():
            raise ValueError("Test error")

        # Mock the logger and ExceptionData
        with (
            patch("mcp_suite.servers.dev.utils.decorators.logger") as mock_logger,
            patch(
                "mcp_suite.servers.dev.models.exception_data.ExceptionData."
                "from_exception"
            ) as mock_from_exception,
        ):

            # Set up the mock to return a known ExceptionData
            mock_exception_data = MagicMock()
            mock_exception_data.model_dump.return_value = {"mocked": "data"}
            mock_from_exception.return_value = mock_exception_data

            # Call the function
            result = sample_function()

            # Check that the logger was called with the expected message
            mock_logger.exception.assert_called_once()
            assert "Error in sample_function" in mock_logger.exception.call_args[0][0]

            # Check the structure of the result
            assert result["Status"] == "Error"
            assert result["Error"] == {"mocked": "data"}
            assert "Instructions" in result

    def test_sync_function_with_reraised_exception(self):
        """Test that a sync function with a reraised exception actually reraises."""

        # Define a function that raises a FileNotFoundError (which should be reraised)
        @exception_handler()
        def sample_function():
            raise FileNotFoundError("Test file not found")

        # The function should raise the exception
        with pytest.raises(FileNotFoundError, match="Test file not found"):
            sample_function()

    def test_sync_function_with_custom_reraise(self):
        """Test that a sync function with a custom reraise list works correctly."""

        # Define a function that raises a ValueError
        @exception_handler(reraise=[ValueError])
        def sample_function():
            raise ValueError("Test error")

        # The function should raise the exception
        with pytest.raises(ValueError, match="Test error"):
            sample_function()

    def test_sync_function_with_custom_log_level(self):
        """Test that a sync function with a custom log level uses that level."""

        # Define a function that raises a TypeError
        @exception_handler(log_level="warning")
        def sample_function():
            raise TypeError("Test type error")

        # Mock the logger
        with patch("mcp_suite.servers.dev.utils.decorators.logger") as mock_logger:
            # Call the function (we don't care about the result)
            sample_function()

            # Check that the warning method was called, not exception
            mock_logger.warning.assert_called_once()
            assert "Error in sample_function" in mock_logger.warning.call_args[0][0]

    @pytest.mark.asyncio
    async def test_async_function_no_exception(self):
        """Test that an async function with no exceptions works normally."""

        # Define a simple async function that doesn't raise exceptions
        @exception_handler()
        async def sample_async_function(x, y):
            await asyncio.sleep(0.01)  # Small delay to ensure it's actually async
            return x * y

        # Call the function and check the result
        result = await sample_async_function(2, 3)
        assert result == 6

    @pytest.mark.asyncio
    async def test_async_function_with_handled_exception(self):
        """Test that an async function with a handled exception returns the expected
        error structure."""

        # Define an async function that raises a RuntimeError
        @exception_handler()
        async def sample_async_function():
            await asyncio.sleep(0.01)  # Small delay
            raise RuntimeError("Async test error")

        # Mock the logger and ExceptionData
        with (
            patch("mcp_suite.servers.dev.utils.decorators.logger") as mock_logger,
            patch(
                "mcp_suite.servers.dev.models.exception_data.ExceptionData."
                "from_exception"
            ) as mock_from_exception,
        ):

            # Set up the mock to return a known ExceptionData
            mock_exception_data = MagicMock()
            mock_exception_data.model_dump.return_value = {"mocked": "async_data"}
            mock_from_exception.return_value = mock_exception_data

            # Call the function
            result = await sample_async_function()

            # Check that the logger was called with the expected message
            mock_logger.exception.assert_called_once()
            assert (
                "Error in sample_async_function"
                in mock_logger.exception.call_args[0][0]
            )

            # Check the structure of the result
            assert result["Status"] == "Error"
            assert result["Error"] == {"mocked": "async_data"}
            assert "Instructions" in result

    @pytest.mark.asyncio
    async def test_async_function_with_reraised_exception(self):
        """Test that an async function with a reraised exception actually reraises."""

        # Define an async function that raises a JSONDecodeError
        # (which should be reraised)
        @exception_handler()
        async def sample_async_function():
            await asyncio.sleep(0.01)  # Small delay
            raise json.JSONDecodeError("Test JSON error", "invalid json", 0)

        # The function should raise the exception
        with pytest.raises(json.JSONDecodeError):
            await sample_async_function()

    @pytest.mark.asyncio
    async def test_async_function_with_custom_reraise(self):
        """Test that an async function with a custom reraise list works correctly."""

        # Define an async function that raises a KeyError
        @exception_handler(reraise=[KeyError])
        async def sample_async_function():
            await asyncio.sleep(0.01)  # Small delay
            raise KeyError("Test key error")

        # The function should raise the exception
        with pytest.raises(KeyError, match="'Test key error'"):
            await sample_async_function()

    @pytest.mark.asyncio
    async def test_async_function_with_custom_log_level(self):
        """Test that an async function with a custom log level uses that level."""

        # Define an async function that raises an IndexError
        @exception_handler(log_level="error")
        async def sample_async_function():
            await asyncio.sleep(0.01)  # Small delay
            raise IndexError("Test index error")

        # Mock the logger
        with patch("mcp_suite.servers.dev.utils.decorators.logger") as mock_logger:
            # Call the function (we don't care about the result)
            await sample_async_function()

            # Check that the error method was called, not exception
            mock_logger.error.assert_called_once()
            assert "Error in sample_async_function" in mock_logger.error.call_args[0][0]

    def test_preserves_function_signature(self):
        """Test that the decorator preserves the original function's signature."""

        # Define a function with a specific signature
        def original_function(a: int, b: str, c: float = 1.0) -> dict:
            return {"a": a, "b": b, "c": c}

        # Apply the decorator
        decorated_function = exception_handler()(original_function)

        # Import inspect to check the signature
        import inspect

        # Get the signatures
        original_sig = inspect.signature(original_function)
        decorated_sig = inspect.signature(decorated_function)

        # Check that they match
        assert str(original_sig) == str(decorated_sig)

        # Check that the parameter annotations are preserved
        for param_name, param in original_sig.parameters.items():
            assert param.annotation == decorated_sig.parameters[param_name].annotation

        # Check that the return annotation is preserved
        assert original_sig.return_annotation == decorated_sig.return_annotation

    def test_exception_data_integration(self):
        """Test that the ExceptionData is correctly created from an exception."""

        # Define a function that raises an exception
        @exception_handler()
        def sample_function():
            # Create a nested call to have a more interesting traceback
            def nested_function():
                raise ValueError("Nested error")

            nested_function()

        # Call the function
        result = sample_function()

        # Check that the ExceptionData was correctly created
        assert result["Status"] == "Error"
        assert "Error" in result
        error_data = result["Error"]

        # Check the error details
        assert error_data["error_type"] == "ValueError"
        assert error_data["error"] == "Nested error"

        # Check that the traceback contains at least one entry
        assert "traceback" in error_data
        assert len(error_data["traceback"]) > 0

        # Check that the traceback entries have the expected structure
        for entry in error_data["traceback"]:
            assert "file_path" in entry
            assert "lineno" in entry
            assert "name" in entry
