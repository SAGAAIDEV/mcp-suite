"""
Configuration package for development servers.
"""

# Import the centralized logger
from mcp_suite.servers.qa import logger

# Import any other configuration modules
from .constants import ReportPaths

# Bind the component field to the logger
logger = logger.bind(component="config")

__all__ = ["logger", "ReportPaths"]
