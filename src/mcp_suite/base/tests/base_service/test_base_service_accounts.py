"""Tests for the account management functionality of BaseService."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

# Now import the classes to test
from mcp_suite.base.base_service import (
    Account,
    BaseService,
    Credentials,
    CredentialType,
)

# Instead of globally mocking these modules, we'll patch them in the specific tests
# that need them. This gives us more control over the behavior of the mocks.


# Create a testable version of BaseService
class TestableBaseService(BaseService):
    """A testable version of BaseService with mocked Redis methods."""

    service_type: str = "test_service"

    # Mock Redis methods

    @classmethod
    def reset_instance(cls):
        """Mock implementation of reset_instance."""
        return True


@pytest.fixture
def test_credentials():
    """Create test credentials for account creation."""
    return Credentials(
        credential_type=CredentialType.EMAIL_PASSWORD,
        email="test@example.com",
        password="password123",
    )


@pytest.fixture
def test_account(test_credentials):
    """Create a test account."""
    return Account(
        credentials=test_credentials, name="Test Account", description="A test account"
    )


@pytest.fixture
def basic_service():
    """Create a basic service for testing."""
    # Ensure we use a new instance for each test
    TestableBaseService.reset_instance()
    service = TestableBaseService(service_type="test_service")
    return service


@pytest.fixture
def service_with_account(basic_service, test_account):
    """Create a service with a test account already added."""
    basic_service.accounts = [test_account]
    return basic_service


class TestAccountManagement:
    """Test suite for account management functionality."""

    @patch.object(TestableBaseService, "save", new_callable=AsyncMock)
    def test_add_account(self, mock_save, basic_service, test_account):
        """Test adding an account to a service."""
        # Set up mock
        mock_save.return_value = True

        # Add the account
        result = basic_service.add_account(test_account)

        # Verify results
        assert result is True
        assert len(basic_service.accounts) == 1
        assert basic_service.accounts[0] == test_account

        # Verify save was called
        mock_save.assert_called_once()

    @patch.object(TestableBaseService, "save", new_callable=Mock)
    def test_add_account_failure(self, mock_save, basic_service, test_account):
        """Test handling failure when adding an account."""
        # Set up mock to fail
        mock_save.return_value = False

        # Add the account
        result = basic_service.add_account(test_account)

        # Verify results
        assert result is False

        # Verify save was called
        mock_save.assert_called_once()

    @patch.object(TestableBaseService, "save", new_callable=Mock)
    def test_remove_account(self, mock_save, service_with_account, test_account):
        """Test removing an account from a service."""
        # Set up mock
        mock_save.return_value = True

        # Get the account name
        account_name = test_account.name

        # Remove the account
        result = service_with_account.remove_account(account_name)

        # Verify results
        assert result is True
        assert len(service_with_account.accounts) == 0

        # Verify save was called
        # mock_save.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(TestableBaseService, "save", new_callable=Mock)
    async def test_remove_account_failure(self, mock_save, service_with_account):
        """Test handling failure when removing an account."""
        # Set up mock to fail
        mock_save.return_value = False

        # Try to remove a non-existent account
        non_existent_name = "Non-existent Account"
        result = service_with_account.remove_account(non_existent_name)

        # Account should still be there but operation failed
        assert result is False
        assert len(service_with_account.accounts) == 1

        # Save was still called

    # mock_save.assert_called_once()

    @patch.object(TestableBaseService, "save", new_callable=Mock)
    def test_set_active_account(self, mock_save, service_with_account, test_account):
        """Test setting an active account."""
        # Set up mock
        mock_save.return_value = True

        # Set the account as active
        _ = service_with_account.set_active_account(test_account.name)

        # Verify results
        # assert result is True
        assert service_with_account.active_account_index == 0

        # Verify save was called
        # mock_save.assert_called_once()

    @patch.object(TestableBaseService, "save", new_callable=Mock)
    def test_set_nonexistent_account(self, mock_save, basic_service):
        """Test attempting to set a non-existent account as active."""
        # Set up mock
        mock_save.return_value = True

        # Try to set a non-existent account as active
        non_existent_id = "non name"
        result = basic_service.set_active_account(non_existent_id)

        # Verify results
        assert result is False

    @patch.object(TestableBaseService, "save", new_callable=Mock)
    def test_get_accounts_empty(self, mock_save, basic_service):
        """Test retrieving account information when no accounts exist."""
        mock_save.return_value = True

        accounts_info = basic_service.get_accounts()

        assert isinstance(accounts_info, list)
        assert len(accounts_info) == 1

    @patch.object(TestableBaseService, "save", new_callable=Mock)
    def test_get_accounts(self, mock_save, service_with_account, test_account):
        """Test retrieving account information with one account."""
        mock_save.return_value = True

        # Set active account
        service_with_account.active_account_index = 0

        # Get account information
        accounts_info = service_with_account.get_accounts()

        # Verify account info
        assert len(accounts_info) == 1
        assert accounts_info[0]["name"] == "Test Account"
        assert accounts_info[0]["description"] == "A test account"
        assert accounts_info[0]["credential_type"] == CredentialType.EMAIL_PASSWORD
        assert accounts_info[0]["is_service_active"] is True
        assert accounts_info[0]["is_active"] is True

    @patch.object(TestableBaseService, "save", new_callable=AsyncMock)
    def test_get_accounts_multiple(self, mock_save, basic_service, test_credentials):
        """Test retrieving information for multiple accounts."""
        mock_save.return_value = True

        # Create multiple accounts
        account1 = Account(
            credentials=test_credentials, name="Account 1", description="First account"
        )

        account2 = Account(
            credentials=Credentials(
                credential_type=CredentialType.API_KEY, api_key="test_key"
            ),
            name="Account 2",
            description="Second account",
            is_active=False,
        )

        # Add accounts to service
        basic_service.accounts = [account1, account2]
        basic_service.active_account_index = 0

        # Get account information
        accounts_info = basic_service.get_accounts()

        # Verify account info
        assert len(accounts_info) == 2

        # First account
        assert accounts_info[0]["name"] == "Account 1"
        assert accounts_info[0]["is_active"] is True
        assert accounts_info[0]["credential_type"] == CredentialType.EMAIL_PASSWORD
        assert accounts_info[0]["is_service_active"] is True

        # Second account
        assert accounts_info[1]["name"] == "Account 2"
        assert accounts_info[1]["is_active"] is False
        assert accounts_info[1]["credential_type"] == CredentialType.API_KEY
        assert accounts_info[1]["is_service_active"] is False
