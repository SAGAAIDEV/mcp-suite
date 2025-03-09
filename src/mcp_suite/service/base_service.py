"""
Base service implementation for MCP Suite.

This module provides the core service classes that all MCP services inherit from.
It includes the BaseService class, Account management, and Credentials handling.
"""

from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Type, Union
from uuid import UUID

from loguru import logger
from pydantic import Field, field_validator, model_validator

from mcp_suite.models.redis_model import RedisModel


class CredentialType(str, Enum):
    """Enum for different types of credentials."""

    EMAIL_PASSWORD = "email_password"
    API_KEY = "api_key"
    OAUTH = "oauth"


class Credentials(RedisModel):
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

    @field_validator("email")
    @classmethod
    def validate_email_for_email_password(
        cls, v: Optional[str], info: Any
    ) -> Optional[str]:
        """Validate that email is provided for EMAIL_PASSWORD credential type."""
        values = info.data
        if values.get("credential_type") == CredentialType.EMAIL_PASSWORD and not v:
            raise ValueError("Email is required for EMAIL_PASSWORD credential type")
        return v

    @field_validator("api_key")
    @classmethod
    def validate_api_key_for_api_key(cls, v: Optional[str], info: Any) -> Optional[str]:
        """Validate that API key is provided for API_KEY credential type."""
        values = info.data
        if values.get("credential_type") == CredentialType.API_KEY and not v:
            raise ValueError("API key is required for API_KEY credential type")
        return v

    @field_validator("oauth_token")
    @classmethod
    def validate_oauth_token_for_oauth(
        cls, v: Optional[str], info: Any
    ) -> Optional[str]:
        """Validate that OAuth token is provided for OAUTH credential type."""
        values = info.data
        if values.get("credential_type") == CredentialType.OAUTH and not v:
            raise ValueError("OAuth token is required for OAUTH credential type")
        return v

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


class Account(RedisModel):
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
                await self.save_to_redis()
                return True
            return False
        except Exception as e:
            logger.error(f"Error testing connection for account {self.id}: {e}")
            return False


class BaseService(RedisModel):
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

    # Class registry to track all service instances
    _service_registry: ClassVar[Dict[str, Type["BaseService"]]] = {}

    # Service metadata
    service_type: str = Field(...)
    accounts: List[Account] = Field(default_factory=list)
    is_enabled: bool = Field(default=True)
    last_active: Optional[datetime] = Field(default=None)
    active_account_index: Optional[int] = Field(default=None)

    @model_validator(mode="after")
    def register_service(self) -> "BaseService":
        """Register this service in the class registry."""
        cls = self.__class__
        service_type = self.service_type

        # Only register if not already registered to prevent recursion
        if service_type not in BaseService._service_registry:
            BaseService._service_registry[service_type] = cls
            logger.info(f"Registered service type: {service_type}")

        # Set last_active timestamp during initialization
        if self.last_active is None:
            self.last_active = datetime.now()

        return self

    @classmethod
    def get_registered_services(cls) -> Dict[str, Type["BaseService"]]:
        """
        Get all registered service types.

        Returns:
            Dictionary of service types to service classes
        """
        return cls._service_registry.copy()

    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all accounts for this service with descriptions.

        Returns:
            List of dictionaries containing account information
        """
        return [
            {
                "id": str(account.id),
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

    async def add_account(self, account: Account) -> bool:
        """
        Add an account to this service.

        Args:
            account: The account to add

        Returns:
            True if successful, False otherwise
        """
        try:
            self.accounts.append(account)
            self.updated_at = datetime.now()
            await self.save_to_redis()
            logger.info(f"Added account {account.id} to service {self.id}")
            return True
        except Exception as e:
            logger.error(f"Error adding account to service {self.id}: {e}")
            return False

    async def remove_account(self, account_id: Union[UUID, str]) -> bool:
        """
        Remove an account from this service.

        Args:
            account_id: The ID of the account to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            account_id_str = str(account_id)
            self.accounts = [a for a in self.accounts if str(a.id) != account_id_str]
            self.updated_at = datetime.now()
            await self.save_to_redis()
            logger.info(f"Removed account {account_id} from service {self.id}")
            return True
        except Exception as e:
            logger.error(f"Error removing account from service {self.id}: {e}")
            return False

    async def service_start(self) -> bool:
        """
        Start the service.

        This method should be called when the service starts up.
        It updates the last_active timestamp and saves to Redis.

        Returns:
            True if start is successful, False otherwise
        """
        try:
            self.last_active = datetime.now()
            await self.save_to_redis()
            logger.info(f"Started service {self.id}")
            return True
        except Exception as e:
            logger.error(f"Error starting service {self.id}: {e}")
            return False

    async def service_stop(self) -> bool:
        """
        Stop the service.

        This method should be called when the service is shutting down.
        It updates the last_active timestamp and saves to Redis.

        Returns:
            True if stop is successful, False otherwise
        """
        try:
            self.last_active = datetime.now()
            await self.save_to_redis()
            logger.info(f"Stopped service {self.id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping service {self.id}: {e}")
            return False

    @classmethod
    async def get_service_by_id(
        cls, service_id: Union[UUID, str]
    ) -> Optional["BaseService"]:
        """
        Get a service instance by ID.

        Args:
            service_id: The ID of the service to get

        Returns:
            Service instance if found, None otherwise
        """
        return await cls.load_from_redis(service_id)

    @classmethod
    async def get_all_services(cls) -> List["BaseService"]:
        """
        Get all service instances.

        Returns:
            List of all service instances
        """
        return await cls.get_all_from_redis()

    async def set_active_account(self, account_id: Union[UUID, str]) -> bool:
        """
        Set an account as the active account for this service.

        Args:
            account_id: The ID of the account to set as active

        Returns:
            True if successful, False otherwise
        """
        try:
            account_id_str = str(account_id)
            for index, account in enumerate(self.accounts):
                if str(account.id) == account_id_str:
                    # Store the index temporarily
                    temp_index = index
                    self.updated_at = datetime.now()

                    # Save to Redis first
                    if await self.save_to_redis():
                        # Only set the index after successful save
                        self.active_account_index = temp_index
                        logger.info(
                            f"Set account {account_id} as active for service {self.id}"
                        )
                        return True
                    else:
                        logger.error(
                            f"Failed to save service {self.id} \
                                  when setting active account"
                        )
                        return False

            logger.warning(f"Account {account_id} not found in service {self.id}")
            return False
        except Exception as e:
            logger.error(f"Error setting active account for service {self.id}: {e}")
            return False
