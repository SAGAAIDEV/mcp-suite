"""Pytest configuration for transcriber tests.

This module contains fixtures and configuration for the transcriber tests.
"""

import sys
from pathlib import Path

import pytest


# Add the project root to the Python path to enable relative imports
@pytest.fixture(scope="session", autouse=True)
def setup_python_path():
    """Add the project root to the Python path to enable relative imports."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent.parent.parent

    # Add the project root to the Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    yield
