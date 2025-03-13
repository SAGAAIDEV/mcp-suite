"""
Configuration package for development servers.
"""

# Import the centralized logger
from src.mcp_suite.servers.dev import logger

# Import any other configuration modules
from .constants import ReportPaths

__all__ = ["logger", "ReportPaths"]
