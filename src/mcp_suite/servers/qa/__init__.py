"""
SaagaLint - A comprehensive linting and testing tool for Python projects.

SaagaLint provides a set of tools for running tests, checking code coverage,
and performing static analysis on Python code. It integrates with pytest,
coverage, and various linting tools to provide a unified interface for
code quality checks.

Components:
- pytest: Run tests and analyze results
- coverage: Check code coverage and identify untested code
- autoflake: Detect and fix unused imports and variables

All logging has been disabled.
"""

from loguru import logger

# Disable all logging
logger.disable("mcp_suite")

# Export the logger for use in other modules (disabled)
__all__ = ["logger"]
