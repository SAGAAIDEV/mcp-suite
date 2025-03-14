"""
Configuration package for development servers.
"""

# Import the centralized logger
from mcp_suite.servers.qa import logger

# Import any other configuration modules
from .constants import ReportPaths

__all__ = ["logger", "ReportPaths"]
