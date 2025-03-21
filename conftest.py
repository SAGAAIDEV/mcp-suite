"""
Root conftest.py file for the entire project.
"""

# Set pytest-asyncio plugin
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """Configure pytest options."""
    # Configure asyncio mode
    config.option.asyncio_mode = "strict"

    # Set the default fixture loop scope to function
    config.option.asyncio_default_fixture_loop_scope = "function"
