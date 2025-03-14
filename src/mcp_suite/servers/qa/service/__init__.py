"""Service functions for the pytest server."""

# Use absolute imports instead of relative imports
# Import the centralized logger
from mcp_suite.servers.qa import logger

from .coverage import process_coverage_json
from .pytest import process_pytest_results

# Bind the component field to the logger
logger = logger.bind(component="service")

__all__ = ["process_coverage_json", "process_pytest_results", "logger"]
