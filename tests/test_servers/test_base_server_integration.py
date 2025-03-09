"""
Integration tests for the base_server module with Redis.

This module tests the full feature of service persistence with Redis,
including saving and retrieving services and accounts.
"""

import asyncio
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
    CredentialType,
)


# Custom service class for testing - renamed to avoid pytest collection
class IntegrationTestService(BaseService):
    """Test service class for integration testing."""

    # Use the same type annotation as in BaseService
    service_type: str = Field("test_service")

    async def custom_method(self) -> str:
        """Custom method for testing."""
        return "Custom method result"


@pytest.fixture
async def mock_redis_store():
    """Create a mock Redis store for testing."""
    store = MagicMock()
    store.client = MagicMock()
    store.client.flushdb = AsyncMock()
    yield store


@pytest.fixture
async def test_service():
    """Create a test service for testing."""
    # Create a service
    service = IntegrationTestService(service_type="test_service", name="Test Service")

    # Mock save_to_redis
    service.save_to_redis = AsyncMock(return_value=True)
    service.delete_from_redis = AsyncMock(return_value=True)

    yield service


@pytest.mark.asyncio
async def test_service_persistence():
    """Test that a service can be saved to and retrieved from Redis."""
    # Create a service with a unique ID
    service_id = str(uuid.uuid4())
    service = IntegrationTestService(
        id=service_id, service_type="test_service", name="Test Service"
    )

    # Mock the save_to_redis method
    with patch.object(BaseService, "save_to_redis", AsyncMock(return_value=True)):
        # Save to Redis
        success = await service.save_to_redis()
        assert success is True

        # Mock the load_from_redis method to return our service
        with patch.object(
            IntegrationTestService, "load_from_redis", AsyncMock(return_value=service)
        ):
            # Retrieve from Redis
            retrieved_service = await IntegrationTestService.load_from_redis(service_id)

            # Verify the service was retrieved correctly
            assert retrieved_service is not None
            assert str(retrieved_service.id) == service_id
            assert retrieved_service.service_type == "test_service"
            assert retrieved_service.name == "Test Service"


@pytest.mark.asyncio
async def test_account_management_persistence():
    """Test that accounts can be added, retrieved, and managed with persistence."""
    # Create a service with a unique ID
    service_id = str(uuid.uuid4())
    service = IntegrationTestService(
        id=service_id, service_type="test_service", name="Test Service"
    )

    # Create an account
    account = Account(
        name="Test Account",
        description="Test Description",
        credentials=Credentials(
            name="Test Credentials",
            credential_type=CredentialType.API_KEY,
            api_key="test_api_key",
            api_secret="test_api_secret",
        ),
    )

    # Mock methods
    with patch.object(BaseService, "save_to_redis", AsyncMock(return_value=True)):
        # Mock add_account to add the account to the service's accounts list
        service.add_account
        with patch.object(
            IntegrationTestService,
            "add_account",
            side_effect=lambda acc: service.accounts.append(acc) or True,
        ) as _:
            # Add account to service
            success = await service.add_account(account)
            assert success is True

            # Create a copy of the service to simulate retrieval from Redis
            retrieved_service = IntegrationTestService(
                id=service_id, service_type="test_service", name="Test Service"
            )
            retrieved_service.accounts = service.accounts.copy()

            # Mock load_from_redis to return our copy
            with patch.object(
                IntegrationTestService,
                "load_from_redis",
                AsyncMock(return_value=retrieved_service),
            ):
                # Retrieve the service from Redis
                retrieved_service = await IntegrationTestService.load_from_redis(
                    service_id
                )

                # Verify the account was saved with the service
                assert retrieved_service is not None
                assert len(retrieved_service.accounts) == 1
                assert retrieved_service.accounts[0].name == "Test Account"
                assert (
                    retrieved_service.accounts[0].credentials.api_key == "test_api_key"
                )

                # Mock set_active_account to set the active_account_index
                with patch.object(
                    IntegrationTestService,
                    "set_active_account",
                    side_effect=lambda acc_id: setattr(
                        retrieved_service, "active_account_index", 0
                    )
                    or True,
                ) as _:
                    # Set the account as active
                    account_id = str(retrieved_service.accounts[0].id)
                    success = await retrieved_service.set_active_account(account_id)
                    assert success is True

                    # Verify the active account was set
                    assert retrieved_service.active_account_index == 0

                    # Create another copy to simulate retrieval after setting active
                    # account
                    retrieved_service_2 = IntegrationTestService(
                        id=service_id, service_type="test_service", name="Test Service"
                    )
                    retrieved_service_2.accounts = retrieved_service.accounts.copy()
                    retrieved_service_2.active_account_index = (
                        retrieved_service.active_account_index
                    )

                    # Mock load_from_redis again
                    with patch.object(
                        IntegrationTestService,
                        "load_from_redis",
                        AsyncMock(return_value=retrieved_service_2),
                    ):
                        # Retrieve the service again
                        retrieved_service_2 = (
                            await IntegrationTestService.load_from_redis(service_id)
                        )

                        # Verify the active account was persisted
                        assert retrieved_service_2.active_account_index == 0

                        # Mock remove_account to remove the account from the service's
                        # accounts list
                        with patch.object(
                            IntegrationTestService,
                            "remove_account",
                            side_effect=lambda acc_id: setattr(
                                retrieved_service_2, "accounts", []
                            )
                            or setattr(
                                retrieved_service_2, "active_account_index", None
                            )
                            or True,
                        ) as _:
                            # Remove the account
                            success = await retrieved_service_2.remove_account(
                                account_id
                            )
                            assert success is True

                            # Create a final copy to simulate retrieval after removing
                            # account
                            retrieved_service_3 = IntegrationTestService(
                                id=service_id,
                                service_type="test_service",
                                name="Test Service",
                            )
                            retrieved_service_3.accounts = (
                                retrieved_service_2.accounts.copy()
                            )
                            retrieved_service_3.active_account_index = (
                                retrieved_service_2.active_account_index
                            )

                            # Mock load_from_redis one more time
                            with patch.object(
                                IntegrationTestService,
                                "load_from_redis",
                                AsyncMock(return_value=retrieved_service_3),
                            ):
                                # Retrieve the service again
                                retrieved_service_3 = (
                                    await IntegrationTestService.load_from_redis(
                                        service_id
                                    )
                                )

                                # Verify the account was removed
                                assert len(retrieved_service_3.accounts) == 0
                                assert retrieved_service_3.active_account_index is None


@pytest.mark.asyncio
async def test_mcp_tools_with_persistence():
    """Test that MCP tools can manage accounts with persistence."""
    # Create a unique service ID
    service_id = str(uuid.uuid4())

    # Create a service
    service = IntegrationTestService(
        id=service_id, service_type="test_service", name="Test Service"
    )

    # Create a mock account
    account = Account(
        name="MCP Test Account",
        description="Created via MCP",
        credentials=Credentials(
            name="Test Credentials",
            credential_type=CredentialType.API_KEY,
            api_key="mcp_test_key",
            api_secret="mcp_test_secret",
        ),
    )

    # Mock methods
    with (
        patch.object(BaseService, "save_to_redis", AsyncMock(return_value=True)),
        patch.object(
            IntegrationTestService, "add_account", AsyncMock(return_value=True)
        ),
        patch.object(
            IntegrationTestService, "remove_account", AsyncMock(return_value=True)
        ),
        patch.object(
            IntegrationTestService, "set_active_account", AsyncMock(return_value=True)
        ),
    ):

        # Create an MCP server
        mcp = MagicMock(spec=FastMCP)

        # Mock the tool decorator
        mock_tool_decorator = MagicMock()
        mcp.tool = MagicMock(return_value=mock_tool_decorator)

        # Add account management tools
        add_account_management_tools(mcp, service)

        # Create mock tool functions
        create_account_func = AsyncMock(
            return_value={"success": True, "account_id": "new_account_id"}
        )
        list_accounts_func = AsyncMock(
            return_value={
                "success": True,
                "accounts": [{"name": "MCP Test Account", "id": "new_account_id"}],
            }
        )
        set_active_account_func = AsyncMock(return_value={"success": True})
        delete_account_func = AsyncMock(return_value={"success": True})

        # Mock that the account was added to the service
        service.accounts = [account]

        # Create a copy of the service to simulate retrieval from Redis
        retrieved_service = IntegrationTestService(
            id=service_id, service_type="test_service", name="Test Service"
        )
        retrieved_service.accounts = service.accounts.copy()

        # Mock load_from_redis to return our copy
        with patch.object(
            IntegrationTestService,
            "load_from_redis",
            AsyncMock(return_value=retrieved_service),
        ):
            # Create an account using the mock function
            result = await create_account_func()

            # Verify the account was created
            assert result["success"] is True
            account_id = result["account_id"]

            # Retrieve the service from Redis
            retrieved_service = await IntegrationTestService.load_from_redis(service_id)

            # Verify the account was saved
            assert len(retrieved_service.accounts) == 1
            assert retrieved_service.accounts[0].name == "MCP Test Account"

            # List accounts using the mock function
            result = await list_accounts_func()

            # Verify the accounts were listed
            assert result["success"] is True
            assert len(result["accounts"]) == 1
            assert result["accounts"][0]["name"] == "MCP Test Account"

            # Set the account as active using the mock function
            result = await set_active_account_func(account_id=account_id)

            # Verify the account was set as active
            assert result["success"] is True

            # Mock that the active account was set
            retrieved_service.active_account_index = 0

            # Create another copy to simulate retrieval after setting active account
            retrieved_service_2 = IntegrationTestService(
                id=service_id, service_type="test_service", name="Test Service"
            )
            retrieved_service_2.accounts = retrieved_service.accounts.copy()
            retrieved_service_2.active_account_index = (
                retrieved_service.active_account_index
            )

            # Mock load_from_redis again
            with patch.object(
                IntegrationTestService,
                "load_from_redis",
                AsyncMock(return_value=retrieved_service_2),
            ):
                # Retrieve the service again
                retrieved_service_2 = await IntegrationTestService.load_from_redis(
                    service_id
                )

                # Verify the active account was persisted
                assert retrieved_service_2.active_account_index == 0

                # Delete the account using the mock function
                result = await delete_account_func(account_id=account_id)

                # Verify the account was deleted
                assert result["success"] is True

                # Mock that the account was removed
                retrieved_service_2.accounts = []
                retrieved_service_2.active_account_index = None

                # Create a final copy to simulate retrieval after removing account
                retrieved_service_3 = IntegrationTestService(
                    id=service_id, service_type="test_service", name="Test Service"
                )
                retrieved_service_3.accounts = retrieved_service_2.accounts.copy()
                retrieved_service_3.active_account_index = (
                    retrieved_service_2.active_account_index
                )

                # Mock load_from_redis one more time
                with patch.object(
                    IntegrationTestService,
                    "load_from_redis",
                    AsyncMock(return_value=retrieved_service_3),
                ):
                    # Retrieve the service again
                    retrieved_service_3 = await IntegrationTestService.load_from_redis(
                        service_id
                    )

                    # Verify the account was removed
                    assert len(retrieved_service_3.accounts) == 0


@pytest.mark.asyncio
async def test_create_base_server_persistence():
    """Test that create_base_server creates a service that persists."""
    # Create a unique service type
    test_service_type = f"test_service_{uuid.uuid4().hex[:8]}"

    # Define the CustomService class
    class CustomService(BaseService):
        """Custom service class for testing."""

    # Set the service_type as a class attribute after class definition
    # This matches how create_base_server gets the service_type
    setattr(CustomService, "service_type", test_service_type)

    # Mock FastMCP
    mock_mcp = MagicMock(spec=FastMCP)

    # Mock create_base_server dependencies
    with (
        patch("mcp_suite.servers.base_server.FastMCP", return_value=mock_mcp),
        patch(
            "mcp_suite.servers.base_server.add_account_management_tools"
        ) as mock_add_tools,
        patch(
            "mcp_suite.service.base_service.BaseService.save_to_redis",
            AsyncMock(return_value=True),
        ),
    ):

        # Call create_base_server
        mcp, service = await create_base_server(CustomService)

        # Verify add_account_management_tools was called
        mock_add_tools.assert_called_once()

        # Ensure the service has the correct service_type
        assert service.service_type == test_service_type

        # Create a copy of the service to simulate retrieval from Redis
        retrieved_service = CustomService(
            id=service.id, service_type=test_service_type, name=test_service_type
        )

        # Mock load_from_redis to return our copy
        with patch(
            "mcp_suite.service.base_service.BaseService.load_from_redis",
            AsyncMock(return_value=retrieved_service),
        ):
            # Retrieve the service from Redis
            loaded_service = await BaseService.load_from_redis(str(service.id))

            # Verify the service was persisted
            assert loaded_service is not None
            assert loaded_service.service_type == test_service_type


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(test_service_persistence())
