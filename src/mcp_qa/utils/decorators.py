"""
Decorators for the SaagaLint MCP server.

This module provides decorators for the SaagaLint MCP server.
"""

import functools
import inspect
import traceback
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from mcp_qa.config import logger
from mcp_qa.models.tool_result import ToolResult, ToolStatus

T = TypeVar("T", bound=Callable[..., Any])


def exception_handler(
    default_return: Optional[Dict[str, Any]] = None,
    reraise: Optional[List[type]] = None,
    log_level: str = "error",
) -> Callable[[T], T]:
    """
    Decorator to handle exceptions in functions.

    This decorator catches any exceptions raised by the decorated function
    and returns a default value instead. It also logs the exception.

    Args:
        default_return: The default value to return if an exception is raised.
                        Defaults to a dictionary with an error message.
        reraise: A list of exception types to re-raise instead of handling.
                 Defaults to None, which means no exceptions are re-raised.
        log_level: The log level to use when logging exceptions.
                   Defaults to "error".

    Returns:
        The decorated function.
    """
    if default_return is None:
        default_return = {
            "Status": "Error",
            "Message": "An unexpected error occurred",
            "Instructions": (
                "Please check the logs for more details. "
                "If the issue persists, contact support."
            ),
        }

    if reraise is None:
        reraise = []

    def decorator(func: T) -> T:
        """
        Decorator function.

        Args:
            func: The function to decorate.

        Returns:
            The decorated function.
        """
        logger.debug(f"Decorating function {func.__name__} with exception_handler")

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function.

            Args:
                *args: Positional arguments to pass to the decorated function.
                **kwargs: Keyword arguments to pass to the decorated function.

            Returns:
                The result of the decorated function, or the default return value
                if an exception is raised.
            """
            try:
                logger.debug(
                    f"Calling function {func.__name__} with "
                    f"args={args}, kwargs={kwargs}"
                )
                return func(*args, **kwargs)
            except Exception as e:
                # Re-raise the exception if it's in the reraise list
                if any(isinstance(e, exc_type) for exc_type in reraise):
                    raise

                # Log the exception with the specified log level
                log_func = getattr(logger, log_level)
                log_func(f"Exception in {func.__name__}: {e}")
                logger.error(traceback.format_exc())
                return default_return

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Async wrapper function.

            Args:
                *args: Positional arguments to pass to the decorated function.
                **kwargs: Keyword arguments to pass to the decorated function.

            Returns:
                The result of the decorated function with appended messages
                based on status.
            """
            try:
                logger.debug(
                    f"Calling async function {func.__name__} with "
                    f"args={args}, kwargs={kwargs}"
                )
                return await func(*args, **kwargs)
            except Exception as e:
                # Re-raise the exception if it's in the reraise list
                if any(isinstance(e, exc_type) for exc_type in reraise):
                    raise

                # Log the exception with the specified log level
                log_func = getattr(logger, log_level)
                log_func(f"Exception in async {func.__name__}: {e}")
                logger.error(traceback.format_exc())
                return default_return

        if inspect.iscoroutinefunction(func):
            logger.debug(f"Function {func.__name__} is a coroutine function")
            return cast(T, async_wrapper)
        else:
            logger.debug(f"Function {func.__name__} is a regular function")
            return cast(T, wrapper)

    return decorator


def tool_flow(
    success_message: Optional[str] = None,
    error_message: Optional[str] = None,
    continue_message: Optional[str] = None,
    failure_message: Optional[str] = None,
    exception_message: Optional[str] = None,
) -> Callable[[T], T]:
    """
    Decorator to append custom messages to ToolResult objects based on their status.

    This decorator examines the ToolResult returned by the decorated function
    and appends specific messages based on the status. This allows for consistent
    messaging across different tools without duplicating code.

    Args:
        success_message: Message to append when status is SUCCESS
        error_message: Message to append when status is ERROR
        continue_message: Message to append when status is CONTINUE
        failure_message: Message to append when status is FAILURE
        exception_message: Message to append when status is EXCEPTION

    Returns:
        The decorated function that will append status-specific messages to the result
    """

    def decorator(func: T) -> T:
        """
        Decorator function.

        Args:
            func: The function to decorate.

        Returns:
            The decorated function.
        """
        logger.debug(f"Decorating function {func.__name__} with status_message_handler")

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function.

            Args:
                *args: Positional arguments to pass to the decorated function.
                **kwargs: Keyword arguments to pass to the decorated function.

            Returns:
                The result of the decorated function with appended messages
                based on status.
            """
            result = func(*args, **kwargs)

            if isinstance(result, ToolResult):
                # Append messages based on status
                if result.status == ToolStatus.SUCCESS and success_message:
                    result.message += f"\n{success_message}"
                elif result.status == ToolStatus.ERROR and error_message:
                    result.message += f"\n{error_message}"
                elif result.status == ToolStatus.CONTINUE and continue_message:
                    result.message += f"\n{continue_message}"
                elif result.status == ToolStatus.FAILURE and failure_message:
                    result.message += f"\n{failure_message}"
                elif result.status == ToolStatus.EXCEPTION and exception_message:
                    result.message += f"\n{exception_message}"

            return result

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Async wrapper function.

            Args:
                *args: Positional arguments to pass to the decorated function.
                **kwargs: Keyword arguments to pass to the decorated function.

            Returns:
                The result of the decorated function with appended messages
                based on status.
            """
            result = await func(*args, **kwargs)

            if isinstance(result, ToolResult):
                # Append messages based on status
                if result.status == ToolStatus.SUCCESS and success_message:
                    result.message += f"\n{success_message}"
                elif result.status == ToolStatus.ERROR and error_message:
                    result.message += f"\n{error_message}"
                elif result.status == ToolStatus.CONTINUE and continue_message:
                    result.message += f"\n{continue_message}"
                elif result.status == ToolStatus.FAILURE and failure_message:
                    result.message += f"\n{failure_message}"
                elif result.status == ToolStatus.EXCEPTION and exception_message:
                    result.message += f"\n{exception_message}"

            return result

        if inspect.iscoroutinefunction(func):
            logger.debug(f"Function {func.__name__} is a coroutine function")
            return cast(T, async_wrapper)
        else:
            logger.debug(f"Function {func.__name__} is a regular function")
            return cast(T, wrapper)

    return decorator
