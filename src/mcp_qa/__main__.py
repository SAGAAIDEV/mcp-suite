"""
Main entry point for the SaagaLint MCP server.

SaagaLint is a comprehensive linting and testing tool for Python projects.
It provides a set of tools for running tests, checking code coverage,
and performing static analysis on Python code.

This module serves as the entry point for the SaagaLint MCP server.
It creates an MCP server instance, registers all tools, and provides
a command-line interface using Google Fire.

Usage:
    # Run with default settings (stdio transport)
    python -m src.mcp_suite.servers.qa

    # Run with SSE transport
    python -m src.mcp_suite.servers.qa --transport=sse

    # Run with SSE transport on a specific host and port
    python -m src.mcp_suite.servers.qa --transport=sse --host=0.0.0.0 --port=8082

    # Run with debug mode enabled
    python -m mcp_qa --debug=True
"""

import datetime
import sys
import traceback

from mcp.server.fastmcp import FastMCP
import contextlib

# Store server start time
SERVER_START_TIME = datetime.datetime.now().isoformat()

try:
    # Import logger and tool registration function
    from mcp_qa.config import logger

    logger.info(f"Server starting at {SERVER_START_TIME}")
    from mcp_qa.tools.register_tools import register_tools

    # Create the MCP server instance
    mcp = FastMCP(
        "precommit", settings={"host": "localhost", "port": 8081, "reload": True}
    )
    logger.info("MCP server instance created")

    # Register all tools
    register_tools(mcp)
    logger.info("All tools registered")
except ModuleNotFoundError as e:
    # Handle import errors specifically
    error_msg = f"Import error: {e}\n{traceback.format_exc()}"
    try:
        # Try to use logger if available
        from mcp_qa.config import logger

        logger.error(error_msg)
    except ImportError:
        # Fallback to printing to stderr if logger import also fails
        print(error_msg, file=sys.stderr)
    sys.exit(1)
except Exception as e:
    # Handle other exceptions
    error_msg = f"Initialization error: {e}\n{traceback.format_exc()}"
    try:
        from mcp_qa.config import logger

        logger.error(error_msg)
    except ImportError:
        print(error_msg, file=sys.stderr)
    sys.exit(1)


def run_server(transport="stdio", host="localhost", port=8081, debug=True):
    """
    Run the SaagaLint MCP server with the specified transport.

    This function configures and starts the MCP server with the specified
    settings. It supports both stdio and SSE transports, and allows
    configuration of host, port, debug mode, and auto-reload.

    Args:
        transport (str): The transport to use. Options are "stdio" or "sse".
        host (str): The host to bind to when using SSE transport.
        port (int): The port to bind to when using SSE transport.
        debug (bool): Whether to enable debug mode.
        reload (bool): Whether to enable auto-reload.

    Returns:
        None
    """
    # Update settings based on parameters
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.settings.debug = debug

    logger.info(
        f"Starting server with transport={transport}, "
        f"host={host}, port={port}, debug={debug}"
    )

    # Run the server with the specified transport
    try:
        logger.info("Server starting...")
        mcp.run(transport=transport)
    except Exception as e:
        logger.exception(f"Server failed to start: {e}")
        raise


import traceback


@contextlib.contextmanager
def log_exceptions(operation_name="operation"):
    try:
        yield
    except ImportError as e:
        logger.error(f"Import error during {operation_name}: {e}")
        logger.error(traceback.format_exc())
        raise  # re-raise after logging
    except Exception as e:
        logger.error(f"Error during {operation_name}: {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":  # pragma: no cover
    # Use Fire to provide a CLI interface
    logger.info("Starting CLI interface with Fire")
    with log_exceptions("Program Start"):
        run_server()
