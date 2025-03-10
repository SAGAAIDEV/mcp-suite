"""
Base service implementation for MCP Suite.

This module provides the core service classes that all MCP services inherit from.
It includes the BaseService class, Account management, and Credentials handling.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from mcp_suite.base.models.redis_singleton import RedisSingleton


class CredentialType(str, Enum):
    """Enum for different types of credentials."""

    EMAIL_PASSWORD = "email_password"
    API_KEY = "api_key"
    OAUTH = "oauth"


class Credentials(BaseModel):
    """
    Base class for service credentials.

    This class handles different types of authentication credentials
    for services, including email/password, API keys, and OAuth.

    Attributes:
        credential_type: The type of credential (email/password, API key, OAuth)
        is_valid: Whether the credentials are valid
        last_validated: When the credentials were last validated
    """

    credential_type: CredentialType
    is_valid: bool = Field(default=False)
    last_validated: Optional[datetime] = Field(default=None)

    # Additional fields for different credential types
    # Email/Password
    email: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)

    # API Key
    api_key: Optional[str] = Field(default=None)
    api_secret: Optional[str] = Field(default=None)

    # OAuth
    oauth_token: Optional[str] = Field(default=None)
    oauth_refresh_token: Optional[str] = Field(default=None)
    oauth_expires_at: Optional[datetime] = Field(default=None)

    # Set model_config to ensure validators run properly
    model_config = ConfigDict(validate_assignment=True)

    @field_serializer("*")
    def serialize_all_datetimes(self, v: Any, _info) -> Any:
        """
        Serialize any datetime field to ISO format string for Redis storage.

        This serializer applies to all fields and only transforms datetime objects.
        Other types are returned as-is.
        """
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @model_validator(mode="after")
    def validate_required_fields(self) -> "Credentials":
        """Validate that required fields are provided based on credential type."""
        if self.credential_type == CredentialType.EMAIL_PASSWORD and not self.email:
            raise ValueError("Email is required for EMAIL_PASSWORD credential type")
        elif self.credential_type == CredentialType.API_KEY and not self.api_key:
            raise ValueError("API key is required for API_KEY credential type")
        elif self.credential_type == CredentialType.OAUTH and not self.oauth_token:
            raise ValueError("OAuth token is required for OAUTH credential type")
        return self

    async def validate(self) -> bool:
        """
        Validate the credentials.

        This method should be overridden by subclasses to implement
        service-specific validation logic.

        Returns:
            True if credentials are valid, False otherwise
        """
        # This is a placeholder - subclasses should implement actual validation
        self.last_validated = datetime.now()
        self.is_valid = True
        return self.is_valid


class Account(BaseModel):
    """
    Account class for service authentication.

    This class represents a user account for a service, containing
    credentials and metadata.

    Attributes:
        credentials: The credentials for this account
        is_active: Whether the account is active
        last_used: When the account was last used
    """

    credentials: Credentials
    is_active: bool = Field(default=True)
    last_used: Optional[datetime] = Field(default=None)
    name: str = Field(default="")
    description: str = Field(default="")

    model_config = ConfigDict(validate_assignment=True)

    @field_validator("credentials")
    @classmethod
    def validate_credentials(cls, v: Any) -> Credentials:
        """
        Validate and convert credentials to a Credentials object if it's a dictionary.

        Args:
            v: Credentials (can be a Credentials object or dictionary)

        Returns:
            Validated Credentials object
        """
        if isinstance(v, dict):
            # Don't trigger auto-save when creating credentials during validation
            return Credentials(**v)

        elif isinstance(v, Credentials):
            return v
        else:
            raise ValueError(
                f"Credentials must be a dict or Credentials object, got {type(v)}"
            )

    async def test_connection(self) -> bool:
        """
        Test the connection to the service using this account.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Validate credentials
            is_valid = await self.credentials.validate()
            if is_valid:
                self.last_used = datetime.now()
                return True
            return False
        except Exception as e:
            logger.error(f"Error testing connection for account {self.name}: {e}")
            return False


class BaseService(RedisSingleton):
    """
    Base class for all MCP services.

    This class provides common functionality for all services,
    including service registration, discovery, and state management.

    Attributes:
        service_type: The type of service
        accounts: List of accounts for this service
        is_enabled: Whether the service is enabled
        last_active: When the service was last active
        active_account_index: The index of the active account in the accounts list
    """

    # Service metadata
    service_type: str = Field(...)
    accounts: List[Account] = Field(default_factory=list)
    is_enabled: bool = Field(default=True)
    last_active: Optional[datetime] = Field(default_factory=datetime.now)
    active_account_index: Optional[int] = Field(default=0)

    model_config = ConfigDict(validate_assignment=True)

    @field_serializer("*")
    def serialize_all_datetimes(self, v: Any, _info) -> Any:
        """
        Serialize any datetime field to ISO format string for Redis storage.

        This serializer applies to all fields and only transforms datetime objects.
        Other types are returned as-is.
        """
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @field_validator("accounts")
    @classmethod
    def validate_accounts(cls, v: List[Any]) -> List[Account]:
        """
        Validate and convert accounts to Account objects if they are dictionaries,
        and ensure credentials within accounts are properly serialized.

        Args:
            v: List of accounts (can be Account objects or dictionaries)

        Returns:
            List of validated Account objects
        """
        result = []
        for item in v:
            if isinstance(item, dict):
                result.append(Account(**item))
            elif isinstance(item, Account):
                # Already an Account object
                result.append(item)
            else:
                raise ValueError(
                    f"Account must be a dict or Account object, got {type(item)}"
                )
        return result

    def enable(self):
        """Enable this service."""
        self.is_enabled = True

    def disable(self):
        """Disable this service."""
        self.is_enabled = False

    def get_mcp_json(self) -> Dict[str, Any]:
        """
        Get MCP server configuration for this service.

        Returns a dictionary representing the MCP configuration for this service,
        which can be incorporated into the main MCP configuration file.

        Returns:
            Dictionary containing the MCP configuration for this service
        """
        # Get service name from class name or service_type
        service_name = self.service_type.lower()

        # Create the base configuration structure
        module_path = (
            f"src.mcp_suite.servers.{service_name}_mcp_server.server.{service_name}"
        )

        # Create the final configuration object
        config = {
            self.__class__.__name__: {
                "command": "uv",
                "args": [
                    "--directory=${MCP_ROOT_DIR}",
                    "run",
                    "python",
                    "-m",
                    module_path,
                ],
            }
        }

        # Return the configuration structure
        return config

    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all accounts for this service with descriptions.

        Returns:
            List of dictionaries containing account information
        """
        return [
            {
                "name": account.name,
                "description": account.description,
                "is_active": account.is_active,
                "credential_type": account.credentials.credential_type,
                "is_valid": account.credentials.is_valid,
                "last_used": (
                    account.last_used.isoformat() if account.last_used else None
                ),
                "is_service_active": index == self.active_account_index,
            }
            for index, account in enumerate(self.accounts)
        ]

    def add_account(self, account: Account) -> bool:
        """
        Add an account to this service.

        Args:
            account: The account to add

        Returns:
            True if successful, False otherwise
        """
        # Validate the account credentials

        # Update the account's last_used timestamp
        account.last_used = datetime.now()

        # Add account to the accounts list
        self.accounts.append(account)

        # Update service last_active timestamp
        self.last_active = datetime.now()

        # Save the updated service
        save_result = self.save()
        if not save_result:
            logger.error("Failed to save service after adding account")
            # Remove the account we just added
            self.accounts.pop()
            return False

        logger.info(f"Successfully  saved {self.__class__.__name__}")
        return True

    def remove_account(self, account_name: str) -> bool:
        """
        Remove an account from this service.

        Args:
            account_name: The name of the account to remove

        Returns:
            True if successful, False otherwise
        """

        # Store original accounts length to check if anything was removed
        accounts = [a.name for a in self.accounts]
        if account_name in accounts:
            index = accounts.index(account_name)
            self.accounts.pop(index)
            save_result = self.save()
            if not save_result:
                logger.error("Failed to save service after removing account")
            return save_result
        else:
            return False

    def set_active_account(self, account_name: str) -> bool:
        """
        Set an account as the active account for this service.

        Args:
            account_name: The name of the account to set as active

        Returns:
            True if successful, False otherwise
        """

        # Find the account with the given name
        account_found = False

        for index, account in enumerate(self.accounts):
            if account.name == account_name:
                # Set active account index
                self.active_account_index = index

                # Update account's last_used timestamp
                account.last_used = datetime.now()

                # Update service's last_active timestamp
                self.last_active = datetime.now()

                account_found = True
                break

        if not account_found:
            logger.warning(
                f"Account '{account_name}' not found in service {self.service_type}"
            )
            return False

        # Save the updated service
        save_result = self.save()
        return save_result
