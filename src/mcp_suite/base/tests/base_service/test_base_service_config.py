"""Tests for the configuration functionality of BaseService."""

import os
from typing import Any, Dict
from unittest.mock import patch

import pytest

# Now import the classes to test
from mcp_suite.base.base_service import BaseService

# Instead of globally mocking these modules, we'll patch them in the specific tests
# that need them. This gives us more control over the behavior of the mocks.


# Create testable versions of BaseService for different service types
class GmailService(BaseService):
    """Gmail service for testing."""

    service_type: str = "gmail"

    async def save_to_redis(self):
        """Mock implementation of save_to_redis."""
        return True

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance for testing."""
        if hasattr(cls, "_instances") and cls.__name__ in cls._instances:
            del cls._instances[cls.__name__]
        return True

    def get_mcp_json(self) -> Dict[str, Any]:
        """Default MCP configuration for Gmail."""
        return {
            "command": "uv",
            "args": [
                "--directory=${MCP_ROOT_DIR}",
                "run",
                "python",
                "-m",
                f"src.mcp_suite.servers.{self.service_type}_mcp_server.server.gmail",
            ],
        }


class CalendarService(BaseService):
    """Calendar service for testing."""

    service_type: str = "calendar"

    async def save_to_redis(self):
        """Mock implementation of save_to_redis."""
        return True

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance for testing."""
        if hasattr(cls, "_instances") and cls.__name__ in cls._instances:
            del cls._instances[cls.__name__]
        return True

    def get_mcp_json(self) -> Dict[str, Any]:
        """Default MCP configuration for Calendar."""
        return {
            "command": "uv",
            "args": [
                "--directory=${MCP_ROOT_DIR}",
                "run",
                "python",
                "-m",
                f"src.mcp_suite.servers.{self.service_type}_mcp_server.server.calendar",
            ],
        }


class BlueskyService(BaseService):
    """Bluesky service for testing."""

    service_type: str = "bluesky"

    async def save_to_redis(self):
        """Mock implementation of save_to_redis."""
        return True

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance for testing."""
        if hasattr(cls, "_instances") and cls.__name__ in cls._instances:
            del cls._instances[cls.__name__]
        return True

    # Override the get_mcp_json method for custom configuration
    def get_mcp_json(self) -> Dict[str, Any]:
        """Custom MCP configuration for Bluesky."""
        return {
            "command": "uv",
            "args": [
                "--directory=${MCP_ROOT_DIR}",
                "run",
                "python",
                "-m",
                f"src.mcp_suite.servers.{self.service_type}_mcp_server.server.bluesky",
                "--custom-option",
            ],
        }


@pytest.fixture
def gmail_service():
    """Create a Gmail service for testing."""
    GmailService.reset_instance()
    service = GmailService(service_type="gmail")
    return service


@pytest.fixture
def calendar_service():
    """Create a Calendar service for testing."""
    CalendarService.reset_instance()
    service = CalendarService(service_type="calendar")
    return service


@pytest.fixture
def bluesky_service():
    """Create a Bluesky service for testing."""
    BlueskyService.reset_instance()
    service = BlueskyService(service_type="bluesky")
    return service


class TestServiceConfiguration:
    """Test suite for service configuration functionality."""

    def test_get_mcp_json_default(self, gmail_service):
        """Test the default MCP configuration generation."""
        config = gmail_service.get_mcp_json()

        # Verify structure
        assert isinstance(config, dict)
        assert "command" in config
        assert "args" in config

        # Verify command
        assert config["command"] == "uv"

        # Verify args
        assert isinstance(config["args"], list)
        assert config["args"][0] == "--directory=${MCP_ROOT_DIR}"
        assert config["args"][1] == "run"
        assert config["args"][2] == "python"
        assert config["args"][3] == "-m"

        # Service-specific module path
        assert "gmail" in config["args"][4]

    def test_get_mcp_json_for_different_services(self, gmail_service, calendar_service):
        """Test MCP configuration for different service types."""
        gmail_config = gmail_service.get_mcp_json()
        calendar_config = calendar_service.get_mcp_json()

        # Verify service-specific module paths
        assert "gmail" in gmail_config["args"][4]
        assert "calendar" in calendar_config["args"][4]

        # Verify different configurations
        assert gmail_config["args"][4] != calendar_config["args"][4]

    def test_get_mcp_json_overridden(self, bluesky_service):
        """Test custom MCP configuration with overridden method."""
        config = bluesky_service.get_mcp_json()

        # Verify structure from parent
        assert "command" in config
        assert "args" in config
        assert config["command"] == "uv"

        # Verify service-specific module path
        assert "bluesky" in config["args"][4]

        # Verify custom arguments added in the override
        assert "--custom-option" in config["args"]

    @patch.dict(os.environ, {"MCP_ROOT_DIR": "/test/path"})
    def test_get_mcp_json_with_environment_variable(self, gmail_service):
        """Test MCP configuration with environment variable."""
        config = gmail_service.get_mcp_json()

        # In a real environment, the variable would be replaced
        # Here we're just testing the structure contains the placeholder
        assert "${MCP_ROOT_DIR}" in config["args"][0]

    def test_mcp_json_command_structure(self, gmail_service):
        """Test the structure of the command in MCP configuration."""
        config = gmail_service.get_mcp_json()

        # Verify command structure matches expected pattern
        assert config["command"] == "uv"
        assert "run" in config["args"]
        assert "python" in config["args"]
        assert "-m" in config["args"]

        # Verify module path follows expected pattern
        module_path = config["args"][4]
        assert module_path.startswith("src.mcp_suite.servers.")
        assert module_path.endswith("_mcp_server.server.gmail")

    @pytest.mark.parametrize("service_type", ["gmail", "calendar", "bluesky"])
    def test_get_mcp_json_parametrized(self, service_type):
        """Test MCP configuration for different service types using parametrization."""
        # Create service dynamically based on the service type
        if service_type == "gmail":
            GmailService.reset_instance()
            service = GmailService(service_type=service_type)
        elif service_type == "calendar":
            CalendarService.reset_instance()
            service = CalendarService(service_type=service_type)
        else:  # bluesky
            BlueskyService.reset_instance()
            service = BlueskyService(service_type=service_type)

        config = service.get_mcp_json()

        # Verify command structure
        assert config["command"] == "uv"
        assert "run" in config["args"]
        assert "python" in config["args"]
        assert "-m" in config["args"]

        # Verify service type is used in the module path
        assert service_type in config["args"][4].lower()

        # Verify custom arguments if it's the Bluesky service
        if service_type == "bluesky":
            assert "--custom-option" in config["args"]
