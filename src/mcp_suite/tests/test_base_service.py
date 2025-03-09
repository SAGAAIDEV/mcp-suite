"""
Tests for the BaseService class.

This module contains tests for the BaseService, Account, and Credentials classes.
"""

import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from mcp_suite.service.base_service import (
    Account,
    BaseService,
    Credentials,
    CredentialType,
)


# Mock the Redis store and model operations
@pytest.fixture(autouse=True)
def mock_redis_operations():
    """Mock Redis operations to avoid actual Redis calls during testing."""
    with (
        patch(
            "mcp_suite.models.redis_model.RedisModel.save_to_redis", return_value=True
        ),
        patch(
            "mcp_suite.models.redis_model.RedisModel.load_from_redis", return_value=None
        ),
        patch(
            "mcp_suite.models.redis_model.RedisModel.delete_from_redis",
            return_value=True,
        ),
        patch(
            "mcp_suite.models.redis_model.RedisModel.exists_in_redis",
            return_value=False,
        ),
        patch(
            "mcp_suite.models.redis_model.RedisModel.get_all_from_redis",
            return_value=[],
        ),
        patch("mcp_suite.models.redis_model.RedisModel.insert", return_value=None),
        patch("mcp_suite.models.redis_model.RedisModel.select", return_value=[]),
        patch("mcp_suite.models.redis_model.RedisModel.delete", return_value=None),
        patch("mcp_suite.models.redis_model.get_redis_store") as mock_get_store,
    ):
        # Create a mock store
        mock_store = MagicMock()
        mock_store.register_model = MagicMock()
        mock_get_store.return_value = mock_store
        yield


@pytest.fixture
def email_credentials():
    """Create email credentials for testing."""
    return Credentials(
        name="Test Email Credentials",
        credential_type=CredentialType.EMAIL_PASSWORD,
        email="test@example.com",
        password="password123",
    )


@pytest.fixture
def api_key_credentials():
    """Create API key credentials for testing."""
    return Credentials(
        name="Test API Key Credentials",
        credential_type=CredentialType.API_KEY,
        api_key="test_api_key",
        api_secret="test_api_secret",
    )


@pytest.fixture
def oauth_credentials():
    """Create OAuth credentials for testing."""
    return Credentials(
        name="Test OAuth Credentials",
        credential_type=CredentialType.OAUTH,
        oauth_token="test_oauth_token",
        oauth_refresh_token="test_refresh_token",
        oauth_expires_at=datetime.now(),
    )


@pytest.fixture
def account(email_credentials):
    """Create an account for testing."""
    return Account(
        name="Test Account",
        description="Test account for unit tests",
        credentials=email_credentials,
    )


@pytest.fixture
def base_service(account):
    """Create a base service for testing."""
    service = BaseService(
        name="Test Service",
        description="Test service for unit tests",
        service_type="test_service",
        accounts=[account],
    )
    return service


@pytest.mark.asyncio
async def test_credentials_validation():
    """Test that credentials validation works."""
    # Email credentials
    email_creds = Credentials(
        name="Email Creds",
        credential_type=CredentialType.EMAIL_PASSWORD,
        email="test@example.com",
        password="password123",
    )
    assert email_creds.email == "test@example.com"

    # API key credentials
    api_creds = Credentials(
        name="API Creds",
        credential_type=CredentialType.API_KEY,
        api_key="test_key",
        api_secret="test_secret",
    )
    assert api_creds.api_key == "test_key"

    # OAuth credentials
    oauth_creds = Credentials(
        name="OAuth Creds",
        credential_type=CredentialType.OAUTH,
        oauth_token="test_token",
        oauth_refresh_token="test_refresh",
    )
    assert oauth_creds.oauth_token == "test_token"

    # Test validation
    is_valid = await email_creds.validate()
    assert is_valid
    assert email_creds.is_valid
    assert email_creds.last_validated is not None


@pytest.mark.asyncio
async def test_account_test_connection(account):
    """Test that account connection testing works."""
    # Test connection
    is_connected = await account.test_connection()
    assert is_connected
    assert account.credentials.is_valid
    assert account.last_used is not None


@pytest.mark.asyncio
async def test_account_test_connection_with_invalid_credentials():
    """Test account connection testing with invalid credentials."""
    # Create credentials
    creds = Credentials(
        name="Invalid Credentials",
        credential_type=CredentialType.API_KEY,
        api_key="invalid_key",
    )

    # Create account
    account = Account(name="Account with Invalid Credentials", credentials=creds)

    # Mock the validate method to return False
    with patch.object(Credentials, "validate", return_value=False):
        # Test connection
        is_connected = await account.test_connection()
        assert not is_connected
        assert not account.credentials.is_valid
        assert account.last_used is None


@pytest.mark.asyncio
async def test_account_test_connection_with_exception():
    """Test account connection testing with an exception during validation."""
    # Create credentials
    creds = Credentials(
        name="Exception Credentials",
        credential_type=CredentialType.API_KEY,
        api_key="exception_key",
    )

    # Create account
    account = Account(name="Account with Exception Credentials", credentials=creds)

    # Mock the validate method to raise an exception
    with patch.object(
        Credentials, "validate", side_effect=Exception("Test validation error")
    ):
        # Test connection
        is_connected = await account.test_connection()
        assert not is_connected


@pytest.mark.asyncio
async def test_base_service_registration():
    """Test that service registration works."""
    # Create a service
    service = BaseService(
        name="Test Service",
        description="Test service for unit tests",
        service_type="test_service",
    )

    # Check registration
    registry = BaseService.get_registered_services()
    assert "test_service" in registry
    assert registry["test_service"] == BaseService

    # Check that last_active was set during initialization
    assert service.last_active is not None


@pytest.mark.asyncio
async def test_base_service_accounts(base_service, api_key_credentials):
    """Test account management in the base service."""
    # Check initial accounts
    accounts = base_service.get_accounts()
    assert len(accounts) == 1
    assert accounts[0]["name"] == "Test Account"

    # Add an account
    new_account = Account(
        name="New Account",
        description="New test account",
        credentials=api_key_credentials,
    )
    success = await base_service.add_account(new_account)
    assert success

    # Check updated accounts
    accounts = base_service.get_accounts()
    assert len(accounts) == 2
    assert accounts[1]["name"] == "New Account"
    assert accounts[1]["credential_type"] == CredentialType.API_KEY

    # Remove an account
    success = await base_service.remove_account(new_account.id)
    assert success

    # Check final accounts
    accounts = base_service.get_accounts()
    assert len(accounts) == 1


@pytest.mark.asyncio
async def test_base_service_lifecycle(base_service):
    """Test service start and stop."""
    # Start service
    success = await base_service.service_start()
    assert success
    assert base_service.last_active is not None

    # Store the last_active timestamp
    last_active = base_service.last_active

    # Wait a moment to ensure timestamp changes
    await asyncio.sleep(0.01)

    # Stop service
    success = await base_service.service_stop()
    assert success
    assert base_service.last_active is not None
    assert base_service.last_active > last_active


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in the service methods."""
    # Create a service
    service = BaseService(
        name="Error Test Service",
        description="Service for testing error handling",
        service_type="error_test",
    )

    # Test add_account with exception
    with patch(
        "mcp_suite.models.redis_model.RedisModel.save_to_redis",
        side_effect=Exception("Test error"),
    ):
        success = await service.add_account(
            Account(
                name="Error Account",
                description="Account for testing errors",
                credentials=Credentials(
                    name="Error Credentials",
                    credential_type=CredentialType.API_KEY,
                    api_key="error_key",
                ),
            )
        )
        assert not success

    # Test remove_account with exception
    with patch(
        "mcp_suite.models.redis_model.RedisModel.save_to_redis",
        side_effect=Exception("Test error"),
    ):
        success = await service.remove_account(uuid4())
        assert not success

    # Test service_start with exception
    with patch(
        "mcp_suite.models.redis_model.RedisModel.save_to_redis",
        side_effect=Exception("Test error"),
    ):
        success = await service.service_start()
        assert not success

    # Test service_stop with exception
    with patch(
        "mcp_suite.models.redis_model.RedisModel.save_to_redis",
        side_effect=Exception("Test error"),
    ):
        success = await service.service_stop()
        assert not success


@pytest.mark.asyncio
async def test_service_static_methods():
    """Test the static methods of the BaseService class."""
    # Test get_service_by_id
    with patch(
        "mcp_suite.models.redis_model.RedisModel.load_from_redis",
        return_value=BaseService(
            name="Found Service",
            description="Service found by ID",
            service_type="found_service",
        ),
    ):
        service = await BaseService.get_service_by_id(uuid4())
        assert service is not None
        assert service.name == "Found Service"

    # Test get_all_services
    with patch(
        "mcp_suite.models.redis_model.RedisModel.get_all_from_redis",
        return_value=[
            BaseService(
                name="Service 1", description="First service", service_type="service_1"
            ),
            BaseService(
                name="Service 2", description="Second service", service_type="service_2"
            ),
        ],
    ):
        services = await BaseService.get_all_services()
        assert len(services) == 2
        assert services[0].name == "Service 1"
        assert services[1].name == "Service 2"


@pytest.mark.asyncio
async def test_credential_validation_errors():
    """Test validation errors for credentials."""
    # Test validation for EMAIL_PASSWORD type
    email_creds = Credentials(
        name="Email Creds",
        credential_type=CredentialType.EMAIL_PASSWORD,
        email="test@example.com",  # Valid email
        password="password123",
    )
    assert email_creds.email == "test@example.com"

    # Test validation for API_KEY type
    api_creds = Credentials(
        name="API Creds",
        credential_type=CredentialType.API_KEY,
        api_key="test_key",  # Valid API key
        api_secret="test_secret",
    )
    assert api_creds.api_key == "test_key"

    # Test validation for OAUTH type
    oauth_creds = Credentials(
        name="OAuth Creds",
        credential_type=CredentialType.OAUTH,
        oauth_token="test_token",  # Valid OAuth token
        oauth_refresh_token="test_refresh",
    )
    assert oauth_creds.oauth_token == "test_token"


@pytest.mark.asyncio
async def test_base_service_registration_with_existing_type():
    """Test that service registration works with an existing service type."""
    # Create a service with a specific type
    service1 = BaseService(
        name="First Service",
        description="First service with this type",
        service_type="duplicate_type",
    )

    # Create another service with the same type
    service2 = BaseService(
        name="Second Service",
        description="Second service with this type",
        service_type="duplicate_type",
    )

    # Check registration - both should be registered but only one entry in registry
    registry = BaseService.get_registered_services()
    assert "duplicate_type" in registry
    assert registry["duplicate_type"] == BaseService

    # Both services should have last_active set
    assert service1.last_active is not None
    assert service2.last_active is not None


@pytest.mark.asyncio
async def test_get_accounts_with_empty_and_null_values():
    """Test the get_accounts method with empty and null values."""
    # Create credentials with minimal data
    creds = Credentials(
        name="Minimal Credentials",
        credential_type=CredentialType.API_KEY,
        api_key="minimal_key",
    )

    # Create account with minimal data and no last_used
    account = Account(name="Minimal Account", credentials=creds)

    # Create service with this account
    service = BaseService(
        name="Minimal Service", service_type="minimal_service", accounts=[account]
    )

    # Get accounts and check the values
    accounts = service.get_accounts()
    assert len(accounts) == 1
    assert accounts[0]["name"] == "Minimal Account"
    assert accounts[0]["description"] is None
    assert accounts[0]["last_used"] is None


@pytest.mark.asyncio
async def test_credential_validation_errors_with_invalid_values():
    """Test validation errors for credentials with invalid values."""
    # Test EMAIL_PASSWORD type with missing email
    with pytest.raises(ValueError) as excinfo:
        Credentials(
            name="Invalid Email Creds",
            credential_type=CredentialType.EMAIL_PASSWORD,
            email=None,  # Missing email
            password="password123",
        )
    assert "Email is required for EMAIL_PASSWORD credential type" in str(excinfo.value)

    # Test API_KEY type with missing api_key
    with pytest.raises(ValueError) as excinfo:
        Credentials(
            name="Invalid API Creds",
            credential_type=CredentialType.API_KEY,
            api_key=None,  # Missing api_key
            api_secret="secret123",
        )
    assert "API key is required for API_KEY credential type" in str(excinfo.value)

    # Test OAUTH type with missing oauth_token
    with pytest.raises(ValueError) as excinfo:
        Credentials(
            name="Invalid OAuth Creds",
            credential_type=CredentialType.OAUTH,
            oauth_token=None,  # Missing oauth_token
            oauth_refresh_token="refresh123",
        )
    assert "OAuth token is required for OAUTH credential type" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_accounts_with_datetime_formatting():
    """Test the get_accounts method with datetime formatting."""
    # Create credentials
    creds = Credentials(
        name="Test Credentials",
        credential_type=CredentialType.API_KEY,
        api_key="test_key",
    )

    # Create account with last_used timestamp
    test_time = datetime.now()
    account_with_timestamp = Account(
        name="Account With Timestamp", credentials=creds, last_used=test_time
    )

    # Create account without last_used timestamp
    account_without_timestamp = Account(
        name="Account Without Timestamp",
        credentials=creds,
        # No last_used set
    )

    # Create service with both accounts
    service = BaseService(
        name="Test Service",
        service_type="test_service",
        accounts=[account_with_timestamp, account_without_timestamp],
    )

    # Get accounts and check the datetime formatting
    accounts = service.get_accounts()
    assert len(accounts) == 2

    # Check account with timestamp
    assert accounts[0]["name"] == "Account With Timestamp"
    assert accounts[0]["last_used"] == test_time.isoformat()
    assert accounts[0]["is_service_active"] is False  # No active account set yet

    # Check account without timestamp
    assert accounts[1]["name"] == "Account Without Timestamp"
    assert accounts[1]["last_used"] is None
    assert accounts[1]["is_service_active"] is False  # No active account set yet


@pytest.mark.asyncio
async def test_set_active_account():
    """Test setting an account as active."""
    # Create credentials
    creds = Credentials(
        name="Test Credentials",
        credential_type=CredentialType.API_KEY,
        api_key="test_key",
    )

    # Create two accounts
    account1 = Account(name="Account 1", credentials=creds)
    account2 = Account(name="Account 2", credentials=creds)

    # Create service with both accounts
    service = BaseService(
        name="Test Service",
        service_type="test_service",
        accounts=[account1, account2],
    )

    # Initially no active account
    assert service.active_account_index is None
    accounts = service.get_accounts()
    assert accounts[0]["is_service_active"] is False
    assert accounts[1]["is_service_active"] is False

    # Set account1 as active
    success = await service.set_active_account(account1.id)
    assert success
    assert service.active_account_index == 0

    # Check that account1 is now active
    accounts = service.get_accounts()
    assert accounts[0]["is_service_active"] is True
    assert accounts[1]["is_service_active"] is False

    # Set account2 as active
    success = await service.set_active_account(account2.id)
    assert success
    assert service.active_account_index == 1

    # Check that account2 is now active
    accounts = service.get_accounts()
    assert accounts[0]["is_service_active"] is False
    assert accounts[1]["is_service_active"] is True

    # Try to set a non-existent account as active
    non_existent_id = uuid4()
    success = await service.set_active_account(non_existent_id)
    assert not success
    assert service.active_account_index == 1  # Unchanged


@pytest.mark.asyncio
async def test_set_active_account_with_exception():
    """Test setting an account as active with an exception."""
    # Create credentials
    creds = Credentials(
        name="Test Credentials",
        credential_type=CredentialType.API_KEY,
        api_key="test_key",
    )

    # Create an account
    account = Account(name="Test Account", credentials=creds)

    # Create service with the account
    service = BaseService(
        name="Test Service",
        service_type="test_service",
        accounts=[account],
    )

    # Test set_active_account with exception
    with patch(
        "mcp_suite.models.redis_model.RedisModel.save_to_redis",
        side_effect=Exception("Test error"),
    ):
        success = await service.set_active_account(account.id)
        assert not success
        assert service.active_account_index is None  # Not set due to exception


@pytest.mark.asyncio
async def test_set_active_account_with_save_failure():
    """Test setting an account as active when save_to_redis returns False."""
    # Create credentials
    creds = Credentials(
        name="Test Credentials",
        credential_type=CredentialType.API_KEY,
        api_key="test_key",
    )

    # Create an account
    account = Account(name="Test Account", credentials=creds)

    # Create service with the account
    service = BaseService(
        name="Test Service",
        service_type="test_service",
        accounts=[account],
    )

    # Test set_active_account with save_to_redis returning False
    with patch(
        "mcp_suite.models.redis_model.RedisModel.save_to_redis",
        return_value=False,
    ):
        success = await service.set_active_account(account.id)
        assert not success
        assert service.active_account_index is None  # Not set due to save failure


if __name__ == "__main__":  # pragma: no cover
    pytest.main(["-xvs", __file__])
