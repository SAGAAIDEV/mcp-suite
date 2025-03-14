"""
Root conftest.py file for the entire project.
"""

import asyncio
import pytest

# Set pytest-asyncio plugin
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Ensure a single event loop for all async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """Configure pytest options."""
    # Configure asyncio mode
    config.option.asyncio_mode = "strict"

    # Filter pydantic warnings
    config.addinivalue_line("filterwarnings", "ignore::DeprecationWarning:pydantic")
