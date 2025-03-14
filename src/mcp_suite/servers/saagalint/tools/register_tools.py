"""Register all tools with the MCP server."""

from mcp.server.fastmcp import FastMCP

from mcp_suite.servers.saagalint.tools.autoflake_tool import run_autoflake
from mcp_suite.servers.saagalint.tools.coverage_tool import run_coverage
from mcp_suite.servers.saagalint.tools.pytest_tool import run_pytest


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server.

    Args:
        mcp: The MCP server instance
    """
    # Register all tools
    mcp.tool()(run_pytest)
    mcp.tool()(run_coverage)
    mcp.tool()(run_autoflake)
