"""Tests for the BlueskyService class."""

import os
from unittest import mock

import pytest
from atproto import Client

from src.mcp_suite.servers.bluesky_mcp_server.model.credentials import (
    BlueskyCredentials,
)
from src.mcp_suite.servers.bluesky_mcp_server.model.service import BlueskyService


@pytest.fixture
def mock_empty_env_vars():
    """Mock empty environment variables for testing."""
    with mock.patch.dict(
        os.environ,
        {},
        clear=True,  # This clears all environment variables
    ):
        yield


@pytest.fixture
def mock_client():
    """Mock the atproto Client."""
    with mock.patch(
        "src.mcp_suite.servers.bluesky_mcp_server.model.service.Client"
    ) as mock_client:
        # Create a mock instance
        client_instance = mock.MagicMock()
        mock_client.return_value = client_instance

        # Mock the session attribute
        client_instance.session = mock.MagicMock()

        # Mock the send_post method
        post_response = mock.MagicMock()
        post_response.uri = "at://test/post/123"
        client_instance.send_post.return_value = post_response

        # Mock the upload_blob method
        upload_response = mock.MagicMock()
        upload_response.blob = {"$type": "blob", "ref": {"$link": "test-link"}}
        client_instance.upload_blob.return_value = upload_response

        yield client_instance


def test_service_init_with_credentials():
    """Test initializing the service with credentials."""
    credentials = BlueskyCredentials(email="user@example.com", password="secret")

    with mock.patch.object(BlueskyService, "authenticate") as mock_auth:
        service = BlueskyService(credentials)
        assert service.credentials == credentials
        mock_auth.assert_called_once()


def test_service_init_without_credentials():
    """Test initializing the service without credentials."""
    with mock.patch.object(BlueskyCredentials, "are_valid", return_value=False):
        with mock.patch.object(BlueskyService, "authenticate") as mock_auth:
            service = BlueskyService()
            assert isinstance(service.credentials, BlueskyCredentials)
            mock_auth.assert_not_called()


def test_authenticate():
    """Test the authenticate method."""
    credentials = BlueskyCredentials(email="user@example.com", password="secret")

    with mock.patch.object(Client, "login") as mock_login:
        service = BlueskyService(credentials)
        # Reset the mock because authenticate is called in __init__
        mock_login.reset_mock()

        service.authenticate()
        mock_login.assert_called_once_with("user@example.com", "secret")


def test_authenticate_invalid_credentials(mock_empty_env_vars):
    """Test authenticate with invalid credentials."""
    # Create empty credentials and bypass the automatic authentication in __init__
    credentials = BlueskyCredentials()

    # Create service with authentication disabled
    with mock.patch.object(BlueskyCredentials, "are_valid", return_value=False):
        service = BlueskyService(credentials)

    # Now test the authenticate method directly
    with pytest.raises(ValueError, match="Credentials are not valid"):
        service.authenticate()


def test_ensure_authenticated(mock_client):
    """Test the ensure_authenticated method."""
    credentials = BlueskyCredentials(email="user@example.com", password="secret")

    with mock.patch.object(BlueskyService, "authenticate") as mock_auth:
        service = BlueskyService(credentials)
        mock_auth.reset_mock()

        # Test with valid session
        mock_client.session = mock.MagicMock()
        service.ensure_authenticated()
        mock_auth.assert_not_called()

        # Test with no session
        mock_client.session = None
        service.ensure_authenticated()
        mock_auth.assert_called_once()


def test_ensure_authenticated_exception():
    """Test the ensure_authenticated method when an exception occurs."""
    credentials = BlueskyCredentials(email="user@example.com", password="secret")

    # Create a service with a properly mocked client
    with mock.patch(
        "src.mcp_suite.servers.bluesky_mcp_server.model.service.Client"
    ) as mock_client_class:
        client_instance = mock.MagicMock()
        # Make sure the client has no session to trigger the authenticate call
        client_instance.session = None
        mock_client_class.return_value = client_instance

        # Create the service
        service = BlueskyService(credentials)

        # Now patch the authenticate method to raise an exception
        with mock.patch.object(service, "authenticate") as mock_auth:
            mock_auth.side_effect = Exception("Authentication error")

            # The ensure_authenticated method should catch this exception and re-raise it
            with pytest.raises(Exception) as excinfo:
                service.ensure_authenticated()

            # Verify the exception message
            assert "Failed to authenticate with Bluesky: Authentication error" in str(
                excinfo.value
            )


def test_post_text(mock_client):
    """Test the post_text method."""
    credentials = BlueskyCredentials(email="user@example.com", password="secret")

    with mock.patch.object(BlueskyService, "ensure_authenticated") as mock_ensure_auth:
        service = BlueskyService(credentials)
        result = service.post_text("Hello, world!")

        mock_ensure_auth.assert_called_once()
        mock_client.send_post.assert_called_once_with("Hello, world!")
        assert result == "at://test/post/123"


def test_post_with_image(mock_client):
    """Test the post_with_image method."""
    credentials = BlueskyCredentials(email="user@example.com", password="secret")
    image_data = b"fake_image_data"

    with mock.patch.object(BlueskyService, "ensure_authenticated") as mock_ensure_auth:
        service = BlueskyService(credentials)
        result = service.post_with_image("Hello with image!", image_data, "Alt text")

        mock_ensure_auth.assert_called_once()
        mock_client.upload_blob.assert_called_once_with(
            image_data, mime_type="image/jpeg"
        )
        mock_client.send_post.assert_called_once_with(
            "Hello with image!",
            images=[
                {"image": mock_client.upload_blob.return_value.blob, "alt": "Alt text"}
            ],
        )
        assert result == "at://test/post/123"
