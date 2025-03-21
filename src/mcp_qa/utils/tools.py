from typing import Callable


def call_tool(func: str | Callable) -> str:
    """
    Generate a message to call an MCP tool by name.

    Args:
        func: Either a callable function or a string representing the function name

    Returns:
        A formatted string indicating which MCP tool to call
    """
    if callable(func):
        func_name = func.__name__
    else:
        func_name = func

    return f"Call mcp tool {func_name}"
