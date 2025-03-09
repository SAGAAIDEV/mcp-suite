"""
Unit tests for the base_server module.

This module tests the functionality of the base_server.py implementation,
including the add_account_management_tools function and create_base_server function.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_suite.servers.base_server import (
    add_account_management_tools,
    create_base_server,
)
from mcp_suite.service.base_service import Account, BaseService, Credentials


@pytest.fixture
def mock_service():
    """Create a mock service for testing."""
    service = MagicMock(spec=BaseService)
    service.service_type = "test_service"
    service.add_account = AsyncMock(return_value=True)
    service.remove_account = AsyncMock(return_value=True)
    service.set_active_account = AsyncMock(return_value=True)
    service.save_to_redis = AsyncMock(return_value=True)

    # Mock accounts
    mock_account = MagicMock(spec=Account)
    mock_account.id = "test_account_id"
    mock_account.name = "Test Account"
    mock_account.credentials = MagicMock(spec=Credentials)

    # Mock accounts list
    mock_accounts = [mock_account]
    service.accounts = mock_accounts
    service.get_accounts.return_value = [
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

    return service


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server for testing."""
    mcp = MagicMock(spec=FastMCP)
    mcp.tool = MagicMock()

    # Mock tool decorator
    mock_tool_decorator = MagicMock()
    mcp.tool.return_value = mock_tool_decorator

    return mcp


@pytest.fixture
def mock_credentials_class():
    """Create a mock Credentials class for testing."""
    with patch("mcp_suite.servers.base_server.Credentials") as mock_creds:
        # Create a mock instance that will be returned when the class is instantiated
        mock_instance = MagicMock(spec=Credentials)
        mock_creds.return_value = mock_instance
        yield mock_creds


@pytest.fixture
def setup_tools(mock_mcp, mock_service, mock_credentials_class):
    """Set up tools and return the decorated functions."""
    with patch("mcp_suite.servers.base_server.Account") as mock_account_class:
        # Create a mock account instance
        mock_account_instance = MagicMock(spec=Account)
        mock_account_instance.id = "new_account_id"
        mock_account_class.return_value = mock_account_instance

        # Add the tools
        add_account_management_tools(mock_mcp, mock_service)

        # Get the tool functions
        create_account_func = mock_mcp.tool.return_value.call_args_list[0][0][0]
        delete_account_func = mock_mcp.tool.return_value.call_args_list[1][0][0]
        set_active_account_func = mock_mcp.tool.return_value.call_args_list[2][0][0]
        list_accounts_func = mock_mcp.tool.return_value.call_args_list[3][0][0]
        update_account_func = mock_mcp.tool.return_value.call_args_list[4][0][0]

        return {
            "create_account": create_account_func,
            "delete_account": delete_account_func,
            "set_active_account": set_active_account_func,
            "list_accounts": list_accounts_func,
            "update_account": update_account_func,
            "mock_account_instance": mock_account_instance,
        }


def test_add_account_management_tools_registers_tools(mock_mcp, mock_service):
    """Test that add_account_management_tools registers all the expected tools."""
    # Call the function
    add_account_management_tools(mock_mcp, mock_service)

    # Check that tool was called for each expected tool
    expected_tools = [
        "create_account",
        "delete_account",
        "set_active_account",
        "list_accounts",
        "update_account",
    ]

    # Verify tool was called for each expected tool
    actual_calls = [call_args[1]["name"] for call_args in mock_mcp.tool.call_args_list]
    for tool_name in expected_tools:
        assert tool_name in actual_calls, f"Tool {tool_name} was not registered"

    # Verify the number of tools registered
    assert (
        len(expected_tools) == mock_mcp.tool.call_count
    ), "Unexpected number of tools registered"


@pytest.mark.asyncio
async def test_create_account_success(mock_service, setup_tools):
    """Test successful account creation."""
    create_account_func = setup_tools["create_account"]
    setup_tools["mock_account_instance"]

    # Call the create_account function
    result = await create_account_func(
        name="New Account",
        description="New Description",
        credential_type="api_key",
        api_key="test_api_key",
    )

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is True
    assert "successfully" in result_dict["message"]
    # assert result_dict["account_id"] == "new_account_id"

    # Verify service method was called
    mock_service.add_account.assert_called_once()


@pytest.mark.asyncio
async def test_create_account_failure(mock_service, setup_tools):
    """Test account creation failure."""
    create_account_func = setup_tools["create_account"]

    # Make add_account return False to simulate failure
    mock_service.add_account.return_value = False

    # Call the create_account function
    result = await create_account_func(
        name="New Account",
        description="New Description",
        credential_type="api_key",
        api_key="test_api_key",
    )

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is False
    assert result_dict["message"] == "Failed to add account to service"

    # Verify service method was called
    mock_service.add_account.assert_called_once()


@pytest.mark.asyncio
async def test_create_account_exception(
    mock_service, setup_tools, mock_credentials_class
):
    """Test account creation with exception."""
    create_account_func = setup_tools["create_account"]

    # Make add_account raise an exception
    mock_service.add_account.side_effect = Exception("Test exception")

    # Call the create_account function
    result = await create_account_func(
        name="New Account",
        description="New Description",
        credential_type="api_key",
        api_key="test_api_key",
    )

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is False
    assert result_dict["message"] == "Error creating account: Test exception"

    # Verify service method was called
    mock_service.add_account.assert_called_once()


@pytest.mark.asyncio
async def test_delete_account_success(mock_service, setup_tools):
    """Test successful account deletion."""
    delete_account_func = setup_tools["delete_account"]

    # Call the delete_account function
    result = await delete_account_func(account_id="test_account_id")

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is True
    assert result_dict["message"] == "Account test_account_id deleted successfully"

    # Verify service method was called
    mock_service.remove_account.assert_called_once_with("test_account_id")


@pytest.mark.asyncio
async def test_delete_account_failure(mock_service, setup_tools):
    """Test account deletion failure."""
    delete_account_func = setup_tools["delete_account"]

    # Make remove_account return False to simulate failure
    mock_service.remove_account.return_value = False

    # Call the delete_account function
    result = await delete_account_func(account_id="test_account_id")

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is False
    assert result_dict["message"] == "Failed to delete account test_account_id"

    # Verify service method was called
    mock_service.remove_account.assert_called_once_with("test_account_id")


@pytest.mark.asyncio
async def test_delete_account_exception(mock_service, setup_tools):
    """Test account deletion with exception."""
    delete_account_func = setup_tools["delete_account"]

    # Make remove_account raise an exception
    mock_service.remove_account.side_effect = Exception("Test exception")

    # Call the delete_account function
    result = await delete_account_func(account_id="test_account_id")

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is False
    assert result_dict["message"] == "Error deleting account: Test exception"

    # Verify service method was called
    mock_service.remove_account.assert_called_once_with("test_account_id")


@pytest.mark.asyncio
async def test_set_active_account_success(mock_service, setup_tools):
    """Test successful setting of active account."""
    set_active_account_func = setup_tools["set_active_account"]

    # Call the set_active_account function
    result = await set_active_account_func(account_id="test_account_id")

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is True
    assert result_dict["message"] == "Account test_account_id set as active"

    # Verify service method was called
    mock_service.set_active_account.assert_called_once_with("test_account_id")


@pytest.mark.asyncio
async def test_set_active_account_failure(mock_service, setup_tools):
    """Test failure to set active account."""
    set_active_account_func = setup_tools["set_active_account"]

    # Make set_active_account return False to simulate failure
    mock_service.set_active_account.return_value = False

    # Call the set_active_account function
    result = await set_active_account_func(account_id="test_account_id")

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is False
    assert result_dict["message"] == "Failed to set account test_account_id as active"

    # Verify service method was called
    mock_service.set_active_account.assert_called_once_with("test_account_id")


@pytest.mark.asyncio
async def test_set_active_account_exception(mock_service, setup_tools):
    """Test setting active account with exception."""
    set_active_account_func = setup_tools["set_active_account"]

    # Make set_active_account raise an exception
    mock_service.set_active_account.side_effect = Exception("Test exception")

    # Call the set_active_account function
    result = await set_active_account_func(account_id="test_account_id")

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is False
    assert result_dict["message"] == "Error setting active account: Test exception"

    # Verify service method was called
    mock_service.set_active_account.assert_called_once_with("test_account_id")


@pytest.mark.asyncio
async def test_list_accounts_success(mock_service, setup_tools):
    """Test successful listing of accounts."""
    list_accounts_func = setup_tools["list_accounts"]

    # Call the list_accounts function
    result = await list_accounts_func()

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is True
    assert result_dict["message"] == "Found 1 accounts"
    assert len(result_dict["accounts"]) == 1
    assert result_dict["accounts"][0]["id"] == "test_account_id"

    # Verify service method was called
    mock_service.get_accounts.assert_called_once()


@pytest.mark.asyncio
async def test_list_accounts_empty(mock_service, setup_tools):
    """Test listing accounts when there are none."""
    list_accounts_func = setup_tools["list_accounts"]

    # Make get_accounts return an empty list
    mock_service.get_accounts.return_value = []

    # Call the list_accounts function
    result = await list_accounts_func()

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is True
    assert result_dict["message"] == "Found 0 accounts"
    assert len(result_dict["accounts"]) == 0

    # Verify service method was called
    mock_service.get_accounts.assert_called_once()


@pytest.mark.asyncio
async def test_list_accounts_exception(mock_service, setup_tools):
    """Test listing accounts with exception."""
    list_accounts_func = setup_tools["list_accounts"]

    # Make get_accounts raise an exception
    mock_service.get_accounts.side_effect = Exception("Test exception")

    # Call the list_accounts function
    result = await list_accounts_func()

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is False
    assert result_dict["message"] == "Error listing accounts: Test exception"
    assert len(result_dict["accounts"]) == 0

    # Verify service method was called
    mock_service.get_accounts.assert_called_once()


@pytest.mark.asyncio
async def test_update_account_success(mock_service, setup_tools):
    """Test successful account update."""
    update_account_func = setup_tools["update_account"]

    # Get the mock account
    mock_account = mock_service.accounts[0]

    # Call the update_account function
    result = await update_account_func(
        account_id="test_account_id",
        name="Updated Name",
        description="Updated Description",
        is_active=True,
        api_key="updated_api_key",
    )

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is True
    assert result_dict["message"] == "Account test_account_id updated successfully"
    assert result_dict["account_id"] == "test_account_id"

    # Verify account fields were updated
    assert mock_account.name == "Updated Name"
    assert mock_account.description == "Updated Description"
    assert mock_account.is_active is True
    assert mock_account.credentials.api_key == "updated_api_key"

    # Verify service method was called
    mock_service.save_to_redis.assert_called_once()


@pytest.mark.asyncio
async def test_update_account_not_found(mock_service, setup_tools):
    """Test updating a non-existent account."""
    update_account_func = setup_tools["update_account"]

    # Call the update_account function with a non-existent account ID
    result = await update_account_func(
        account_id="non_existent_id",
        name="Updated Name",
    )

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is False
    assert result_dict["message"] == "Account non_existent_id not found"

    # Verify service method was not called
    mock_service.save_to_redis.assert_not_called()


@pytest.mark.asyncio
async def test_update_account_save_failure(mock_service, setup_tools):
    """Test account update with save failure."""
    update_account_func = setup_tools["update_account"]

    # Make save_to_redis return False to simulate failure
    mock_service.save_to_redis.return_value = False

    # Call the update_account function
    result = await update_account_func(
        account_id="test_account_id",
        name="Updated Name",
    )

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is False
    assert result_dict["message"] == "Failed to update account"

    # Verify service method was called
    mock_service.save_to_redis.assert_called_once()


@pytest.mark.asyncio
async def test_update_account_exception(mock_service, setup_tools):
    """Test account update with exception."""
    update_account_func = setup_tools["update_account"]

    # Make save_to_redis raise an exception
    mock_service.save_to_redis.side_effect = Exception("Test exception")

    # Call the update_account function
    result = await update_account_func(
        account_id="test_account_id",
        name="Updated Name",
    )

    # Convert result to dict for easier assertions
    result_dict = json.loads(json.dumps(result))

    # Verify the result
    assert result_dict["success"] is False
    assert result_dict["message"] == "Error updating account: Test exception"

    # Verify service method was called
    mock_service.save_to_redis.assert_called_once()


@pytest.mark.asyncio
async def test_create_base_server():
    """Test creating a base server."""
    with (
        patch("mcp_suite.servers.base_server.FastMCP") as mock_fastmcp_class,
        patch(
            "mcp_suite.servers.base_server.add_account_management_tools"
        ) as mock_add_tools,
    ):

        # Create mock objects
        mock_mcp = MagicMock(spec=FastMCP)
        mock_fastmcp_class.return_value = mock_mcp

        # Create a mock service class
        mock_service_class = MagicMock(spec=type)
        mock_service_class.service_type = "test_service"

        # Create a mock service instance
        mock_service = MagicMock(spec=BaseService)
        mock_service.save_to_redis = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service

        # Call create_base_server
        mcp, service = await create_base_server(mock_service_class)

        # Verify FastMCP was created with the correct service type
        mock_fastmcp_class.assert_called_once_with("test_service")

        # Verify service was created with the correct parameters
        mock_service_class.assert_called_once_with(
            service_type="test_service", name="test_service"
        )

        # Verify service was saved to Redis
        mock_service.save_to_redis.assert_called_once()

        # Verify add_account_management_tools was called
        mock_add_tools.assert_called_once_with(mock_mcp, mock_service)

        # Verify the returned values
        assert mcp == mock_mcp
        assert service == mock_service


@pytest.mark.asyncio
async def test_create_base_server_with_class_name():
    """Test creating a base server with class name as service type."""
    with (
        patch("mcp_suite.servers.base_server.FastMCP") as mock_fastmcp_class,
        patch(
            "mcp_suite.servers.base_server.add_account_management_tools"
        ) as mock_add_tools,
    ):

        # Create mock objects
        mock_mcp = MagicMock(spec=FastMCP)
        mock_fastmcp_class.return_value = mock_mcp

        # Create a mock service class without service_type
        mock_service_class = MagicMock(spec=type)
        mock_service_class.__name__ = "TestService"
        # Remove service_type attribute
        if hasattr(mock_service_class, "service_type"):
            delattr(mock_service_class, "service_type")

        # Create a mock service instance
        mock_service = MagicMock(spec=BaseService)
        mock_service.save_to_redis = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service

        # Call create_base_server
        mcp, service = await create_base_server(mock_service_class)

        # Verify FastMCP was created with the lowercase class name
        mock_fastmcp_class.assert_called_once_with("testservice")

        # Verify service was created with the correct parameters
        mock_service_class.assert_called_once_with(
            service_type="testservice", name="testservice"
        )

        # Verify service was saved to Redis
        mock_service.save_to_redis.assert_called_once()

        # Verify add_account_management_tools was called
        mock_add_tools.assert_called_once_with(mock_mcp, mock_service)

        # Verify the returned values
        assert mcp == mock_mcp
        assert service == mock_service
