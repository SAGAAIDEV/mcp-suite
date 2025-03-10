"""Tests for the Credentials class."""

# Mock the RedisSingleton import in base_service.py
# This is needed because base_service.py imports RedisSingleton but we don't need it for testing Credentials
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from mcp_suite.base.base_service import Credentials, CredentialType

# Mock the imports that are causing issues
sys.modules["mcp_suite.base.models.redis_singleton"] = MagicMock()
sys.modules["mcp_suite.base.models.redis"] = MagicMock()
sys.modules["mcp_suite.models.redis"] = MagicMock()
sys.modules["mcp_suite.models.redis_singleton"] = MagicMock()

# Now we can import from base_service safely


class TestCredentials:
    """Test suite for the Credentials class."""

    def test_base_credential_initialization(self):
        """Test that a credential can be initialized with the required fields."""
        # Email/Password credential type
        credentials = Credentials(
            credential_type=CredentialType.EMAIL_PASSWORD,
            email="user@example.com",
            password="password123",
        )

        assert credentials.credential_type == CredentialType.EMAIL_PASSWORD
        assert credentials.email == "user@example.com"
        assert credentials.password == "password123"
        assert credentials.is_valid is False  # Default value
        assert credentials.last_validated is None  # Default value

    def test_email_password_credential_properties(self):
        """Test properties of email/password credentials."""
        # Valid email/password credential
        credentials = Credentials(
            credential_type=CredentialType.EMAIL_PASSWORD,
            email="user@example.com",
            password="password123",
        )
        assert credentials.email == "user@example.com"
        assert credentials.password == "password123"

        # Other credential types don't require email
        api_cred = Credentials(credential_type=CredentialType.API_KEY, api_key="key123")
        assert api_cred.email is None

    def test_api_key_credential_properties(self):
        """Test properties of API key credentials."""
        # Valid API key credential
        credentials = Credentials(
            credential_type=CredentialType.API_KEY,
            api_key="key123",
            api_secret="secret123",
        )
        assert credentials.api_key == "key123"
        assert credentials.api_secret == "secret123"

        # Other credential types don't require API key
        email_cred = Credentials(
            credential_type=CredentialType.EMAIL_PASSWORD,
            email="user@example.com",
            password="password123",
        )
        assert email_cred.api_key is None

    def test_oauth_credential_properties(self):
        """Test properties of OAuth credentials."""
        # Valid OAuth credential
        now = datetime.now()
        credentials = Credentials(
            credential_type=CredentialType.OAUTH,
            oauth_token="token123",
            oauth_refresh_token="refresh123",
            oauth_expires_at=now,
        )
        assert credentials.oauth_token == "token123"
        assert credentials.oauth_refresh_token == "refresh123"
        assert credentials.oauth_expires_at == now

        # Other credential types don't require OAuth token
        email_cred = Credentials(
            credential_type=CredentialType.EMAIL_PASSWORD,
            email="user@example.com",
            password="password123",
        )
        assert email_cred.oauth_token is None

    @pytest.mark.asyncio
    @patch("mcp_suite.base.base_service.datetime")
    async def test_validate_method(self, mock_datetime):
        """Test the validate method."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        credentials = Credentials(
            credential_type=CredentialType.EMAIL_PASSWORD,
            email="user@example.com",
            password="password123",
        )

        # Before validation
        assert credentials.is_valid is False
        assert credentials.last_validated is None

        # After validation
        result = await credentials.validate()
        assert result is True
        assert credentials.is_valid is True
        assert credentials.last_validated == mock_now

    def test_multiple_credential_types_initialization(self):
        """Test that providing fields for multiple credential types is allowed."""
        # Create a credential with fields for multiple types
        credentials = Credentials(
            credential_type=CredentialType.EMAIL_PASSWORD,
            email="user@example.com",
            password="password123",
            api_key="key123",
            oauth_token="token123",
        )

        assert credentials.credential_type == CredentialType.EMAIL_PASSWORD
        assert credentials.email == "user@example.com"
        assert credentials.api_key == "key123"
        assert credentials.oauth_token == "token123"

    def test_email_validation_raises_error(self):
        """Test that creating EMAIL_PASSWORD credentials without email raises ValueError."""
        with pytest.raises(
            ValueError, match="Email is required for EMAIL_PASSWORD credential type"
        ):
            Credentials(
                credential_type=CredentialType.EMAIL_PASSWORD,
                password="password123",
            )

    def test_api_key_validation_raises_error(self):
        """Test that creating API_KEY credentials without api_key raises ValueError."""
        with pytest.raises(
            ValueError, match="API key is required for API_KEY credential type"
        ):
            Credentials(
                credential_type=CredentialType.API_KEY,
                api_secret="secret123",
            )

    def test_oauth_token_validation_raises_error(self):
        """Test that creating OAUTH credentials without oauth_token raises ValueError."""
        with pytest.raises(
            ValueError, match="OAuth token is required for OAUTH credential type"
        ):
            Credentials(
                credential_type=CredentialType.OAUTH,
                oauth_refresh_token="refresh123",
            )

    def test_datetime_serialization(self):
        """Test that datetime fields are properly serialized to ISO format."""
        # Create a specific datetime for testing
        test_datetime = datetime(2023, 5, 15, 14, 30, 45)

        # Create credentials with the datetime
        credentials = Credentials(
            credential_type=CredentialType.OAUTH,
            oauth_token="token123",
            oauth_refresh_token="refresh123",
            oauth_expires_at=test_datetime,
        )

        # Convert to dict using model_dump() which triggers serializers
        serialized_data = credentials.model_dump()

        # Verify the datetime was serialized to ISO format string
        assert isinstance(serialized_data["oauth_expires_at"], str)
        assert serialized_data["oauth_expires_at"] == test_datetime.isoformat()

        # Original object should still have datetime object
        assert isinstance(credentials.oauth_expires_at, datetime)
        assert credentials.oauth_expires_at == test_datetime
