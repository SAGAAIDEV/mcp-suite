"""Main entry point for the SaagaLint MCP server."""

import datetime

import fire
from mcp.server.fastmcp import FastMCP

# Import logging configuration
from mcp_suite.servers.saagalint import logger

# Import tool registration function
from mcp_suite.servers.saagalint.tools.register_tools import register_tools

# Store server start time
SERVER_START_TIME = datetime.datetime.now().isoformat()

# Create the MCP server instance
mcp = FastMCP("precommit", settings={"host": "localhost", "port": 8081, "reload": True})

# Register all tools
register_tools(mcp)


def run_server(
    transport="stdio", host="localhost", port=8081, debug=False, reload=True
):
    """
    Run the SaagaLint MCP server with the specified transport.

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

    # Update settings based on parameters
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.settings.debug = debug

    # Run the server with the specified transport
    try:
        mcp.run(transport=transport)
    except Exception as e:
        logger.exception(f"Error running MCP server: {e}")
        raise


if __name__ == "__main__":  # pragma: no cover
    # Use Fire to provide a CLI interface
    fire.Fire(run_server)
