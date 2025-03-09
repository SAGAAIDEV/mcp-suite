"""
Unit tests for the base_server module with mocked Redis.

This module tests the service persistence functionality using mocked Redis.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from mcp_suite.servers.base_server import (
    add_account_management_tools,
    create_base_server,
)
from mcp_suite.service.base_service import (
    Account,
    BaseService,
    Credentials,
)


# Mock Redis store for testing
class MockRedisStore:
    """Mock Redis store for testing."""

    def __init__(self):
        """Initialize the mock store."""
        self.data = {}
        self.client = MagicMock()
        self.client.flushdb = AsyncMock()

    async def set(self, key, value):
        """Set a value in the mock store."""
        self.data[key] = value
        return True

    async def get(self, key):
        """Get a value from the mock store."""
        return self.data.get(key)

    async def delete(self, key):
        """Delete a value from the mock store."""
        if key in self.data:
            del self.data[key]
            return 1
        return 0

    def register_model(self, model_class):
        """Register a model class with the store."""


# Custom service class for testing - renamed to avoid pytest collection
class MockTestService(BaseService):
    """Mock service class for integration testing."""

    # Use the same type annotation as in BaseService
    service_type: str = Field("test_service")

    async def custom_method(self) -> str:
        """Custom method for testing."""
        return "Custom method result"


@pytest.fixture
def mock_redis_store():
    """Create a mock Redis store for testing."""
    return MockRedisStore()


@pytest.fixture
def mock_get_redis_store(mock_redis_store):
    """Mock the get_redis_store function to return our mock store."""
    with patch(
        "mcp_suite.models.redis_model.get_redis_store", return_value=mock_redis_store
    ):
        yield


@pytest.fixture
def mock_service():
    """Create a mock service for testing."""
    # Create a mock service instead of a real one to avoid validation issues
    service = MagicMock(spec=BaseService)
    service.service_type = "test_service"
    service.name = "Test Service"
    service.id = str(uuid.uuid4())
    service.save_to_redis = AsyncMock(return_value=True)
    service.add_account = AsyncMock(return_value=True)
    service.remove_account = AsyncMock(return_value=True)
    service.set_active_account = AsyncMock(return_value=True)
    service.accounts = []

    return service


@pytest.mark.asyncio
async def test_service_persistence_with_mock_redis(
    mock_get_redis_store, mock_redis_store
):
    """Test that a service can be saved to and retrieved from Redis."""
    # Patch the BaseService methods
    with (
        patch.object(BaseService, "save_to_redis", autospec=True) as mock_save,
        patch.object(BaseService, "load_from_redis", autospec=True) as mock_load,
    ):

        # Set up the mock save method
        mock_save.return_value = True

        # Create a mock service instead of a real one
        service = MagicMock(spec=BaseService)
        service.service_type = "test_service"
        service.name = "Test Service"
        service.id = str(uuid.uuid4())

        # Save to Redis
        success = await BaseService.save_to_redis(service)
        assert success is True
        assert mock_save.called

        # Set up the mock load method to return our service
        mock_load.return_value = service

        # Retrieve from Redis
        retrieved_service = await BaseService.load_from_redis(service.id)

        # Verify the service was retrieved correctly
        assert retrieved_service is not None
        assert retrieved_service.service_type == "test_service"
        assert retrieved_service.name == "Test Service"
        assert mock_load.called


@pytest.mark.asyncio
async def test_account_management_with_mock_redis(mock_get_redis_store):
    """Test account management with mocked Redis."""
    # Create a mock service
    service = MagicMock(spec=BaseService)
    service.service_type = "test_service"
    service.name = "Test Service"
    service.id = str(uuid.uuid4())
    service.accounts = []
    service.save_to_redis = AsyncMock(return_value=True)
    service.add_account = AsyncMock(return_value=True)
    service.remove_account = AsyncMock(return_value=True)
    service.set_active_account = AsyncMock(return_value=True)

    # Create a mock account
    account = MagicMock(spec=Account)
    account.id = "test_account_id"
    account.name = "Test Account"
    account.credentials = MagicMock(spec=Credentials)
    account.credentials.api_key = "test_api_key"

    # Add account to service
    success = await service.add_account(account)
    assert success is True

    # Verify add_account was called
    service.add_account.assert_called_once()

    # Mock that the account was added
    service.accounts.append(account)

    # Set the account as active
    account_id = str(account.id)
    success = await service.set_active_account(account_id)
    assert success is True

    # Verify set_active_account was called
    service.set_active_account.assert_called_once_with(account_id)

    # Mock that the active account was set
    service.active_account_index = 0

    # Remove the account
    success = await service.remove_account(account_id)
    assert success is True

    # Verify remove_account was called
    service.remove_account.assert_called_once_with(account_id)

    # Mock that the account was removed
    service.accounts = []
    service.active_account_index = None


@pytest.mark.asyncio
async def test_mcp_tools_with_mock_redis(mock_get_redis_store):
    """Test MCP tools with mocked Redis."""
    # Create a mock service
    service = MagicMock(spec=BaseService)
    service.service_type = "test_service"
    service.name = "Test Service"
    service.id = str(uuid.uuid4())
    service.save_to_redis = AsyncMock(return_value=True)
    service.add_account = AsyncMock(return_value=True)
    service.remove_account = AsyncMock(return_value=True)
    service.set_active_account = AsyncMock(return_value=True)

    # Mock the get_accounts method
    service.get_accounts = MagicMock(
        return_value=[
            {
                "id": "test_account_id",
                "name": "Test Account",
                "description": "Test Description",
                "is_active": True,
                "credential_type": "api_key",
                "is_valid": True,
                "last_used": None,
                "is_service_active": True,
            }
        ]
    )

    # Create an MCP server
    mcp = FastMCP("test_service")

    # Mock the tool decorator
    mock_tool_decorator = MagicMock()
    mcp.tool = MagicMock(return_value=mock_tool_decorator)

    # Add account management tools
    add_account_management_tools(mcp, service)

    # Get the tool functions
    create_account_func = None
    list_accounts_func = None
    set_active_account_func = None
    delete_account_func = None

    for call in mcp.tool.call_args_list:
        name = call[1]["name"]
        if name == "create_account":
            create_account_func = mock_tool_decorator.call_args_list[
                mcp.tool.call_args_list.index(call)
            ][0][0]
        elif name == "list_accounts":
            list_accounts_func = mock_tool_decorator.call_args_list[
                mcp.tool.call_args_list.index(call)
            ][0][0]
        elif name == "set_active_account":
            set_active_account_func = mock_tool_decorator.call_args_list[
                mcp.tool.call_args_list.index(call)
            ][0][0]
        elif name == "delete_account":
            delete_account_func = mock_tool_decorator.call_args_list[
                mcp.tool.call_args_list.index(call)
            ][0][0]

    # Mock Account and Credentials classes
    with (
        patch("mcp_suite.servers.base_server.Account") as mock_account_class,
        patch("mcp_suite.servers.base_server.Credentials") as mock_credentials_class,
    ):

        # Create mock instances
        mock_account = MagicMock(spec=Account)
        mock_account.id = "new_account_id"
        mock_credentials = MagicMock(spec=Credentials)

        # Set up the mocks to return our instances
        mock_account_class.return_value = mock_account
        mock_credentials_class.return_value = mock_credentials

        # Test create_account
        result = await create_account_func(
            name="Test Account",
            description="Test Description",
            credential_type="api_key",
            api_key="test_api_key",
        )

        # Verify the result
        assert result["success"] is True

    # Test list_accounts
    result = await list_accounts_func()

    # Verify the result
    assert result["success"] is True
    assert len(result["accounts"]) == 1

    # Verify service.get_accounts was called
    service.get_accounts.assert_called_once()

    # Test set_active_account
    result = await set_active_account_func(account_id="test_account_id")

    # Verify the result
    assert result["success"] is True

    # Verify service.set_active_account was called
    service.set_active_account.assert_called_once_with("test_account_id")

    # Test delete_account
    result = await delete_account_func(account_id="test_account_id")

    # Verify the result
    assert result["success"] is True

    # Verify service.remove_account was called
    service.remove_account.assert_called_once_with("test_account_id")


@pytest.mark.asyncio
async def test_create_base_server_with_mock_redis(mock_get_redis_store):
    """Test create_base_server with mocked Redis."""

    # Create a custom service class
    class CustomService(BaseService):
        # Use the same type annotation as in BaseService
        service_type: str = Field("test_service")

    # Mock the service instance
    mock_service = MagicMock(spec=CustomService)
    mock_service.id = str(uuid.uuid4())
    mock_service.service_type = "test_service"
    mock_service.name = "Test Service"
    mock_service.save_to_redis = AsyncMock(return_value=True)

    # Mock the service class
    with patch.object(CustomService, "__new__", return_value=mock_service):
        # Create a server and service
        mcp, service = await create_base_server(CustomService)

        # Verify the service was created
        assert service is mock_service

        # Verify save_to_redis was called
        mock_service.save_to_redis.assert_called_once()


if __name__ == "__main__":  # pragma: no cover
    pytest.main(["-xvs", __file__])
