"""Service functions for the pytest server."""

# Use absolute imports instead of relative imports

# Import the centralized logger
from mcp_suite.servers.qa import logger

from .coverage import process_coverage_json
from .pytest_service import process_pytest_results

__all__ = ["process_coverage_json", "process_pytest_results", "logger"]
