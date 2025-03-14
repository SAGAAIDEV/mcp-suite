"""Utility decorators for the dev server.

This module provides decorators that enhance MCP server tools with
self-repair capabilities. The primary decorator, `exception_handler`,
wraps MCP tool functions to automatically handle exceptions and prevent
server crashes.

Key features of the exception_handler:

1. Self-Repair Mechanism:
   - Catches exceptions that would normally crash the MCP server
   - Transforms errors into structured responses with detailed diagnostics
   - Allows the server to continue operating despite tool failures
   - Provides guidance for resolving the underlying issues

2. Exception Handling Strategy:
   - Some exceptions (FileNotFoundError, JSONDecodeError) are re-raised by default
   - All other exceptions are caught and transformed into structured responses
   - Captures complete traceback information for debugging
   - Logs errors for later analysis

3. Response Structure:
   - Status: Indicates an error occurred
   - Error: Detailed error information including traceback, error type, and message
   - Instructions: Helpful guidance for resolving the issue

4. Usage:
   Apply the decorator to any MCP tool function:
   ```python
   @mcp.tool()
   @exception_handler()
   async def my_tool_function():
       # Function implementation that might raise exceptions
   ```

This decorator is particularly valuable in AI-assisted development
environments where AI can use the structured error information to suggest
fixes without requiring manual intervention when tools fail.
"""

import functools
import inspect
import json
import sys
from typing import Callable, List, Type, TypeVar

from mcp_suite.servers.saagalint import log_file, logger
from mcp_suite.servers.saagalint.models.exception_data import ExceptionData

# Define a generic type for the return value
T = TypeVar("T")


def exception_handler(
    reraise: List[Type[Exception]] = None,
    log_level: str = "exception",
):
    """
    Decorator that provides self-repair capabilities to MCP tool functions.

    This decorator wraps functions to catch exceptions, transform them into structured
    responses, and prevent the MCP server from crashing. It's designed to make MCP
    tools more resilient and provide helpful diagnostic information when errors occur.

    Features:
    - Catches exceptions and prevents server crashes
    - Captures detailed traceback information
    - Logs errors for debugging
    - Returns structured error responses with guidance
    - Works with both synchronous and asynchronous functions

    Args:
        reraise: List of exception types to re-raise instead of handling.
                Default: [FileNotFoundError, json.JSONDecodeError]
        log_level: Logging level to use for exceptions (default: "exception")

    Returns:
        A decorator function that wraps the target function with error handling

    Example:
        @mcp.tool()
        @exception_handler()
        async def divide(x: int, y: int):
            return x / y
    """
    reraise = reraise or [FileNotFoundError, json.JSONDecodeError]

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Preserve the original signature
        sig = inspect.signature(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except tuple(reraise) as e:
                # Log the error with the specified level
                getattr(logger, log_level)(f"{type(e).__name__}: {e}")
                # Re-raise the exception
                raise
            except Exception as e:
                # Get exception info
                exc_type, exc_value, exc_traceback = sys.exc_info()

                # Log the error with the specified level
                getattr(logger, log_level)(f"Error in {func.__name__}: {e}")
                # Return the default value
                return {
                    "Status": "Error",
                    "Error": ExceptionData.from_exception(
                        exc_type, exc_value, exc_traceback
                    ).model_dump(),
                    "Instructions": (
                        f"Oops! We encountered an unexpected error while "
                        f"running pytest. Don't worry, these things happen! "
                        f"Check the logs for details in {log_file}, and we'll "
                        f"figure out what went wrong together. Every error is "
                        f"an opportunity to learn something new. 1. Explain what "
                        f"happened where it happend, identify where the exception "
                        f"occured and then fix the code that is broke. The call "
                        f"the mcp tool reload"
                    ),
                }

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except tuple(reraise) as e:
                # Log the error with the specified level
                getattr(logger, log_level)(f"{type(e).__name__}: {e}")
                # Re-raise the exception
                raise
            except Exception as e:
                # Get exception info
                exc_type, exc_value, exc_traceback = sys.exc_info()

                # Log the error with the specified level
                getattr(logger, log_level)(f"Error in {func.__name__}: {e}")
                # Return the default value
                return {
                    "Status": "Error",
                    "Error": ExceptionData.from_exception(
                        exc_type, exc_value, exc_traceback
                    ).model_dump(),
                    "Instructions": (
                        f"Oops! We encountered an unexpected error while "
                        f"running pytest. Don't worry, these things happen! "
                        f"Check the logs for details in {log_file}, and we'll "
                        f"figure out what went wrong together. Every error is "
                        f"an opportunity to learn something new. 1. Explain what "
                        f"happened where it happend, identify where the exception "
                        f"occured and then fix the code that is broke. The call "
                        f"the mcp tool reload"
                    ),
                }

        # Choose the appropriate wrapper based on whether the function is async or not
        wrapper = async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

        # Ensure the wrapper has the same signature as the original function
        wrapper.__signature__ = sig

        return wrapper

    return decorator
