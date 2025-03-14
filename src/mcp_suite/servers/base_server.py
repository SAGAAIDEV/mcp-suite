"""Base MCP Server

This module provides a function to add base service account management tools
to an existing FastMCP server. This allows for easy extension of any MCP server
with account management functionality.

Usage:
    Import the add_account_management_tools function and apply it to your server:
    ```python
    from mcp.server.fastmcp import FastMCP
    from mcp_suite.servers.base_server import add_account_management_tools
    from your_service.model import YourService

    # Create your MCP server
    mcp = FastMCP("your_service_name")

    # Initialize your service
    service = YourService(service_type="your_service", name="Your Service")
    await service.save_to_redis()

    # Add your specialized tools
    @mcp.tool(name="my_specialized_tool")
    async def my_specialized_tool():
        # Tool implementation
        pass

    # Add account management tools to the server
    add_account_management_tools(mcp, service)

    # Run the server
    if __name__ == "__main__":
        mcp.run(transport="stdio")
    ```
"""

from typing import Dict, Optional, Type

from loguru import logger
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from mcp_suite.base.base_service import Account, BaseService, Credentials


class AccountResponse(BaseModel):
    """Response model for account operations."""

    success: bool
    message: str
    account_id: Optional[str] = None


def add_account_management_tools(mcp: FastMCP, service: BaseService) -> None:
    """
    Add account management tools to an existing FastMCP server.

    Args:
        mcp: The FastMCP server to add tools to
        service: An initialized service instance that inherits from BaseService
    """
    # Get the service type from the instance
    service_type = service.service_type

    @mcp.tool(
        name="create_account",
        description=f"Create a new account for the {service_type} service",
    )
    async def create_account(
        name: str,
        description: Optional[str] = None,
        credential_type: str = "api_key",
        email: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        oauth_token: Optional[str] = None,
        oauth_refresh_token: Optional[str] = None,
    ) -> Dict:
        """
        Create a new account for this service.

        Args:
            name: Name for the account
            description: Optional description
            credential_type: Type of credentials (email_password, api_key, oauth)
            email: Email for email/password auth
            password: Password for email/password auth
            api_key: API key for API key auth
            api_secret: API secret for API key auth
            oauth_token: OAuth token for OAuth auth
            oauth_refresh_token: OAuth refresh token for OAuth auth

        Returns:
            Response with success status, message, and account ID
        """
        try:
            # Create credentials based on type
            credentials = Credentials(
                credential_type=credential_type,
                email=email,
                password=password,
                api_key=api_key,
                api_secret=api_secret,
                oauth_token=oauth_token,
                oauth_refresh_token=oauth_refresh_token,
            )

            # Create account
            account = Account(
                name=name, description=description, credentials=credentials
            )

            # Add account to service
            success = await service.add_account(account)

            if success:
                return AccountResponse(
                    success=True,
                    message=f"Account {name} created successfully",
                    account_id=str(account.id),
                ).model_dump()
            else:
                return AccountResponse(
                    success=False, message="Failed to add account to service"
                ).model_dump()

        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return AccountResponse(
                success=False, message=f"Error creating account: {str(e)}"
            ).model_dump()

    @mcp.tool(
        name="delete_account",
        description=f"Delete an account from the {service_type} service",
    )
    async def delete_account(account_id: str) -> Dict:
        """
        Delete an account from this service.

        Args:
            account_id: ID of the account to delete

        Returns:
            Response with success status and message
        """
        try:
            # Remove account
            success = await service.remove_account(account_id)

            if success:
                return AccountResponse(
                    success=True, message=f"Account {account_id} deleted successfully"
                ).model_dump()
            else:
                return AccountResponse(
                    success=False, message=f"Failed to delete account {account_id}"
                ).model_dump()

        except Exception as e:
            logger.error(f"Error deleting account: {e}")
            return AccountResponse(
                success=False, message=f"Error deleting account: {str(e)}"
            ).model_dump()

    @mcp.tool(
        name="set_active_account",
        description=f"Set an account as active for the {service_type} service",
    )
    async def set_active_account(account_id: str) -> Dict:
        """
        Set an account as the active account for this service.

        Args:
            account_id: ID of the account to set as active

        Returns:
            Response with success status and message
        """
        try:
            # Set active account
            success = await service.set_active_account(account_id)

            if success:
                return AccountResponse(
                    success=True, message=f"Account {account_id} set as active"
                ).model_dump()
            else:
                return AccountResponse(
                    success=False,
                    message=f"Failed to set account {account_id} as active",
                ).model_dump()

        except Exception as e:
            logger.error(f"Error setting active account: {e}")
            return AccountResponse(
                success=False, message=f"Error setting active account: {str(e)}"
            ).model_dump()

    @mcp.tool(
        name="list_accounts",
        description=f"List all accounts for the {service_type} service",
    )
    async def list_accounts() -> Dict:
        """
        List all accounts for this service.

        Returns:
            Dictionary with accounts list and success status
        """
        try:
            # Get accounts
            accounts = service.get_accounts()

            return {
                "success": True,
                "message": f"Found {len(accounts)} accounts",
                "accounts": accounts,
            }

        except Exception as e:
            logger.error(f"Error listing accounts: {e}")
            return {
                "success": False,
                "message": f"Error listing accounts: {str(e)}",
                "accounts": [],
            }

    @mcp.tool(
        name="update_account",
        description=f"Update an account for the {service_type} service",
    )
    async def update_account(
        account_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        oauth_token: Optional[str] = None,
        oauth_refresh_token: Optional[str] = None,
    ) -> Dict:
        """
        Update an existing account for this service.

        Args:
            account_id: ID of the account to update
            name: New name for the account
            description: New description
            is_active: Whether the account is active
            email: New email for email/password auth
            password: New password for email/password auth
            api_key: New API key for API key auth
            api_secret: New API secret for API key auth
            oauth_token: New OAuth token for OAuth auth
            oauth_refresh_token: New OAuth refresh token for OAuth auth

        Returns:
            Response with success status and message
        """
        try:
            # Find the account
            account_id_str = str(account_id)
            account = None

            for acc in service.accounts:
                if str(acc.id) == account_id_str:
                    account = acc
                    break

            if not account:
                return AccountResponse(
                    success=False, message=f"Account {account_id} not found"
                ).model_dump()

            # Update account fields
            if name is not None:
                account.name = name
            if description is not None:
                account.description = description
            if is_active is not None:
                account.is_active = is_active

            # Update credentials fields
            if email is not None:
                account.credentials.email = email
            if password is not None:
                account.credentials.password = password
            if api_key is not None:
                account.credentials.api_key = api_key
            if api_secret is not None:
                account.credentials.api_secret = api_secret
            if oauth_token is not None:
                account.credentials.oauth_token = oauth_token
            if oauth_refresh_token is not None:
                account.credentials.oauth_refresh_token = oauth_refresh_token

            # Save the service
            success = await service.save_to_redis()

            if success:
                return AccountResponse(
                    success=True,
                    message=f"Account {account_id} updated successfully",
                    account_id=account_id_str,
                ).model_dump()
            else:
                return AccountResponse(
                    success=False, message="Failed to update account"
                ).model_dump()

        except Exception as e:
            logger.error(f"Error updating account: {e}")
            return AccountResponse(
                success=False, message=f"Error updating account: {str(e)}"
            ).model_dump()


async def create_base_server(
    service_class: Type[BaseService],
) -> tuple[FastMCP, BaseService]:
    """
    Create a FastMCP server with base service account management tools.

    Args:
        service_class: The service class that inherits from BaseService

    Returns:
        A tuple containing (mcp_server, service_instance)
    """
    # Get the service type from the class
    service_type = getattr(
        service_class, "service_type", service_class.__name__.lower()
    )

    # Create the FastMCP server
    mcp = FastMCP(service_type)

    # Initialize the service
    service = service_class(service_type=service_type, name=service_type)
    await service.save_to_redis()

    # Add account management tools
    add_account_management_tools(mcp, service)

    # Return both the server and the service
    return mcp, service


if __name__ == "__main__":  # pragma: no cover
    # Example usage
    import asyncio

    # Create a custom service class
    class ExampleService(BaseService):
        service_type = "example"

        # You can add custom methods and attributes here
        async def custom_method(self):
            return "Custom method result"

    async def test_server():
        # Method 1: Create a new server with account management tools
        mcp1, service1 = await create_base_server(ExampleService)
        print(
            f"Created server with account management tools for service: {service1.id}"
        )

        # Method 2: Create a server and add account management tools separately
        mcp2 = FastMCP("example")

        # Initialize service manually
        service2 = ExampleService(service_type="example", name="Example Service")
        await service2.save_to_redis()

        @mcp2.tool(name="custom_tool")
        async def custom_tool(param: str) -> str:
            return f"Custom tool executed with param: {param}"

        add_account_management_tools(mcp2, service2)
        print(
            f"Added account management tools to existing server for service: {
                service2.id}"
        )

        # In a real scenario, you would run one of the servers
        # mcp1.run(transport="stdio")

    asyncio.run(test_server())
