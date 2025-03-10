"""Tests for the Account class."""

# Mock the RedisSingleton import in base_service.py to avoid import errors
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from mcp_suite.base.base_service import Account, Credentials, CredentialType

# Mock the imports that are causing issues
sys.modules["mcp_suite.base.models.redis_singleton"] = MagicMock()
sys.modules["mcp_suite.base.models.redis"] = MagicMock()
sys.modules["mcp_suite.models.redis"] = MagicMock()
sys.modules["mcp_suite.models.redis_singleton"] = MagicMock()

# Now we can import from base_service safely


# Create a custom Account class for testing
class AccountTestable(Account):
    """A testable version of Account with mocked Redis methods."""

    async def save_to_redis(self):
        """Mock implementation of save_to_redis."""
        return True

    def auto_save_on_change(self):
        """Mock implementation of auto_save_on_change."""
        return self


class TestAccount:
    """Test suite for the Account class."""

    def test_account_initialization(self):
        """Test that an Account can be initialized with required fields."""
        # Create credentials for the account
        credentials = Credentials(
            credential_type=CredentialType.EMAIL_PASSWORD,
            email="user@example.com",
            password="password123",
        )

        # Initialize account with credentials
        account = AccountTestable(credentials=credentials)

        # Verify initialization
        assert account.credentials == credentials
        assert account.is_active is True  # Default value
        assert account.last_used is None  # Default value

    def test_account_with_custom_values(self):
        """Test account initialization with non-default values."""
        # Create credentials
        credentials = Credentials(
            credential_type=CredentialType.API_KEY,
            api_key="api_key_123",
            api_secret="secret_456",
        )

        # Set a specific last_used time
        last_used = datetime(2023, 1, 1, 12, 0, 0)

        # Initialize account with custom values
        account = AccountTestable(
            credentials=credentials,
            is_active=False,
            last_used=last_used,
        )

        # Verify initialization with custom values
        assert account.credentials == credentials
        assert account.is_active is False
        assert account.last_used == last_used

    def test_credentials_access(self):
        """Test that credential properties can be accessed through the account."""
        # Create OAuth credentials
        credentials = Credentials(
            credential_type=CredentialType.OAUTH,
            oauth_token="token_123",
            oauth_refresh_token="refresh_456",
        )

        # Initialize account
        account = AccountTestable(credentials=credentials)

        # Verify credential properties can be accessed through the account
        assert account.credentials.credential_type == CredentialType.OAUTH
        assert account.credentials.oauth_token == "token_123"
        assert account.credentials.oauth_refresh_token == "refresh_456"

    @pytest.mark.asyncio
    @patch.object(Credentials, "validate")
    async def test_test_connection_success(self, mock_validate):
        """Test the test_connection method when validation succeeds."""
        # Setup mock to return True (successful validation)
        mock_validate.return_value = True

        # Create credentials
        credentials = Credentials(
            credential_type=CredentialType.EMAIL_PASSWORD,
            email="user@example.com",
            password="password123",
        )

        # Initialize account with name and description
        account = AccountTestable(
            credentials=credentials,
            name="Test Account",
            description="Test account description",
        )

        # Test the connection
        result = await account.test_connection()

        # Verify the result
        assert result is True
        # Verify the validation method was called
        mock_validate.assert_called_once()
        # Verify last_used was updated
        assert account.last_used is not None
        # Verify name and description were set correctly
        assert account.name == "Test Account"
        assert account.description == "Test account description"

    @pytest.mark.asyncio
    @patch.object(Credentials, "validate")
    async def test_test_connection_failure(self, mock_validate):
        """Test the test_connection method when validation fails."""
        # Setup mock to return False (failed validation)
        mock_validate.return_value = False

        # Create credentials
        credentials = Credentials(
            credential_type=CredentialType.EMAIL_PASSWORD,
            email="user@example.com",
            password="password123",
        )

        # Initialize account with name
        account = AccountTestable(credentials=credentials, name="Failed Account")

        # Set initial last_used time
        initial_time = datetime(2023, 1, 1, 12, 0, 0)
        account.last_used = initial_time

        # Test the connection
        result = await account.test_connection()

        # Verify the result
        assert result is False
        # Verify the validation method was called
        mock_validate.assert_called_once()
        # Verify last_used was not updated
        assert account.last_used == initial_time
        # Verify name was set correctly
        assert account.name == "Failed Account"

    @pytest.mark.asyncio
    @patch.object(Credentials, "validate")
    async def test_test_connection_exception(self, mock_validate):
        """Test the test_connection method when an exception occurs during validation."""
        # Setup mock to raise an exception
        mock_validate.side_effect = Exception("Validation error")

        # Create credentials
        credentials = Credentials(
            credential_type=CredentialType.EMAIL_PASSWORD,
            email="user@example.com",
            password="password123",
        )

        # Initialize account with name and description
        account = AccountTestable(
            credentials=credentials,
            name="Exception Account",
            description="Account that throws exception",
        )

        # Set initial last_used time
        initial_time = datetime(2023, 1, 1, 12, 0, 0)
        account.last_used = initial_time

        # Test the connection
        result = await account.test_connection()

        # Verify the result
        assert result is False
        # Verify the validation method was called
        mock_validate.assert_called_once()
        # Verify last_used was not updated
        assert account.last_used == initial_time
        # Verify name and description were set correctly
        assert account.name == "Exception Account"
        assert account.description == "Account that throws exception"
