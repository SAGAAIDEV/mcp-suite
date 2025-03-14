"""
Tool registration for the SaagaLint MCP server.

This module provides a function to register all tools with the MCP server.
Each tool is imported from its respective module and registered with the
MCP server using the tool() decorator.

Available tools:
- run_pytest: Run pytest tests and analyze results
- run_coverage: Check code coverage and identify untested code
- run_autoflake: Detect and fix unused imports and variables
- run_flake8: Check code style and quality using flake8
"""

from mcp.server.fastmcp import FastMCP

from mcp_suite.servers.qa.tools.autoflake_tool import run_autoflake
from mcp_suite.servers.qa.tools.coverage_tool import run_coverage
from mcp_suite.servers.qa.tools.flake8_tool import run_flake8
from mcp_suite.servers.qa.tools.pytest_tool import run_pytest

# Remove logger imports and initialization
# from mcp_suite.servers.qa import logger
# Bind the component field to the logger
# logger = logger.bind(component="tools")


def register_tools(mcp: FastMCP) -> None:
    """
    Register all tools with the MCP server.

    This function registers each tool with the MCP server using the tool()
    decorator. Each tool is imported from its respective module and registered
    with the MCP server.

    Args:
        mcp: The MCP server instance
    """
    # Register pytest tool
    mcp.tool()(run_pytest)

    # Register coverage tool
    mcp.tool()(run_coverage)

    # Register autoflake tool
    mcp.tool()(run_autoflake)

    # Register flake8 tool
    mcp.tool()(run_flake8)
