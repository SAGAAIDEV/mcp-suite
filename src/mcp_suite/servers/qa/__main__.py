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
    python -m src.mcp_suite.servers.qa --debug=True
"""

import datetime
from pathlib import Path

import fire
from mcp.server.fastmcp import FastMCP

# Import logging configuration
from mcp_suite.servers.qa import logger

# Import tool registration function
from mcp_suite.servers.qa.tools.register_tools import register_tools

# Store server start time
SERVER_START_TIME = datetime.datetime.now().isoformat()
logger.info(f"SaagaLint server starting at {SERVER_START_TIME}")

# Create logs directory if it doesn't exist
log_path = Path(__file__).parent / "logs"
log_path.mkdir(exist_ok=True)
logger.info(f"Logs directory: {log_path}")

# Create the MCP server instance
logger.info("Creating MCP server instance")
mcp = FastMCP("precommit", settings={"host": "localhost", "port": 8081, "reload": True})

# Register all tools
register_tools(mcp)


def run_server(transport="stdio", host="localhost", port=8081, debug=False):
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
    logger.info(f"Starting SaagaLint MCP server with {transport} transport")
    logger.info(f"Server configuration: host={host}, port={port}, debug={debug}")

    # Update settings based on parameters
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.settings.debug = debug

    # Run the server with the specified transport
    try:
        logger.info(f"Running MCP server with {transport} transport")
        mcp.run(transport=transport)
    except Exception as e:
        logger.exception(f"Error running MCP server: {e}")
        raise


if __name__ == "__main__":  # pragma: no cover
    # Use Fire to provide a CLI interface
    logger.info("Starting SaagaLint server via command line")
    fire.Fire(run_server)
