"""Bluesky service model.

This module defines the service class for interacting with Bluesky.
"""

from typing import Optional

from atproto import Client

from src.mcp_suite.servers.bluesky_mcp_server.model.credentials import (
    BlueskyCredentials,
)


class BlueskyService:
    """Bluesky service for interacting with the Bluesky social network.

    This class handles authentication and provides methods for posting
    content to Bluesky.
    """

    def __init__(self, credentials: Optional[BlueskyCredentials] = None):
        """Initialize the Bluesky service.

        Args:
            credentials: Optional BlueskyCredentials instance. If not provided,
                         credentials will be loaded from environment variables.
        """
        self.client = Client()
        self.credentials = credentials or BlueskyCredentials()

        # Try to authenticate if credentials are available
        if self.credentials.are_valid():
            self.authenticate()

    def authenticate(self) -> None:
        """Authenticate with Bluesky using the provided credentials."""
        if not self.credentials.are_valid():
            raise ValueError(
                "Credentials are not valid. \
                Please set them before authenticating."
            )

        self.client.login(self.credentials.email, self.credentials.password)

    def ensure_authenticated(self) -> None:
        """Ensure we have an active Bluesky session."""
        try:
            # Check if we need to login
            if not hasattr(self.client, "session") or not self.client.session:
                self.authenticate()
        except Exception as e:
            raise Exception(f"Failed to authenticate with Bluesky: {str(e)}")

    def post_text(self, text: str) -> str:
        """Post text content to Bluesky.

        Args:
            text: The text content to post

        Returns:
            The URI of the created post
        """
        self.ensure_authenticated()
        post = self.client.send_post(text)
        return post.uri

    def post_with_image(
        self, text: str, image_data: bytes, alt_text: Optional[str] = None
    ) -> str:
        """Post text content with an image to Bluesky.

        Args:
            text: The text content to post
            image_data: Raw image data
            alt_text: Optional alternative text for the image

        Returns:
            The URI of the created post
        """
        self.ensure_authenticated()

        # Upload the image
        upload = self.client.upload_blob(image_data, mime_type="image/jpeg")

        # Create post with image
        post = self.client.send_post(
            text, images=[{"image": upload.blob, "alt": alt_text or text}]
        )

        return post.uri
