"""
Tool registration for the SaagaLint MCP server.

This module provides a function to register all tools with the MCP server.
Each tool is imported from its respective module and registered with the
MCP server using the tool() decorator.

Available tools:
- run_pytest: Run pytest tests and analyze results
- run_coverage: Check code coverage and identify untested code
- run_autoflake: Detect and fix unused imports and variables
"""

from mcp.server.fastmcp import FastMCP

from mcp_suite.servers.saagalint import logger
from mcp_suite.servers.saagalint.tools.autoflake_tool import run_autoflake
from mcp_suite.servers.saagalint.tools.coverage_tool import run_coverage
from mcp_suite.servers.saagalint.tools.pytest_tool import run_pytest


def register_tools(mcp: FastMCP) -> None:
    """
    Register all tools with the MCP server.

    This function registers each tool with the MCP server using the tool()
    decorator. Each tool is imported from its respective module and registered
    with the MCP server.

    Args:
        mcp: The MCP server instance
    """
    logger.info("Registering SaagaLint tools with MCP server")

    # Register pytest tool
    logger.debug("Registering run_pytest tool")
    mcp.tool()(run_pytest)

    # Register coverage tool
    logger.debug("Registering run_coverage tool")
    mcp.tool()(run_coverage)

    # Register autoflake tool
    logger.debug("Registering run_autoflake tool")
    mcp.tool()(run_autoflake)

    logger.info("All SaagaLint tools registered successfully")
