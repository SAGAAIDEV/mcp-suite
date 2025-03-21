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

from mcp_qa.config.tools import (
    clear_logs,
    get_current_log_file,
    read_log,
)
from mcp_qa.tools.formatter.formatter_tool import formatter
from mcp_qa.tools.linter.flake8_report import flake8_report
from mcp_qa.tools.linter.pylint_tool import pylint_report
from mcp_qa.tools.testing.coverage_report import (
    run_coverage,
)
from mcp_qa.tools.testing.pytest_report import generate_test_reports
from mcp_qa.tools.testing.utils.make_test import (
    create_test_file,
    source_to_test_path,
)

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
    # Register formatter tool
    mcp.tool()(formatter)

    # Run flake8 report
    mcp.tool()(flake8_report)

    # Register pytest tool
    mcp.tool()(generate_test_reports)
    mcp.tool()(create_test_file)
    mcp.tool()(source_to_test_path)

    # # Register coverage tool
    # mcp.tool()(next_coverage_issue)

    # Register coverage tool
    mcp.tool()(run_coverage)

    # Register pylint tool
    mcp.tool()(pylint_report)

    # Register logging tools
    mcp.tool()(read_log)
    mcp.tool()(clear_logs)
    mcp.tool()(get_current_log_file)
