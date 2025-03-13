"""
Constants for the development server.
"""

from enum import Enum
from pathlib import Path


class ReportPaths(str, Enum):
    """Enum for report file paths."""

    PYTEST_RESULTS = Path("./reports/pytest_results.json")
    FAILED_TESTS = Path("./reports/failed_tests.json")
    COVERAGE = Path("./reports/coverage.json")
    AUTOFLAKE = Path("./reports/autoflake.json")
