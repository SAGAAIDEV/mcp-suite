"""Bluesky credentials model.

This module defines the Pydantic model for Bluesky credentials.
"""

import os
from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator


class BlueskyCredentials(BaseModel):
    """Bluesky credentials model.

    This model represents the credentials needed to authenticate with Bluesky.
    It can be initialized with email and password directly, or it can load them
    from environment variables.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    email: Optional[str] = None
    password: Optional[str] = None

    @model_validator(mode="after")
    def load_from_env_if_empty(self) -> "BlueskyCredentials":
        """Load credentials from environment if they are not provided."""
        if self.email is None:
            self.email = os.getenv("BLUESKY_EMAIL")

        if self.password is None:
            self.password = os.getenv("BLUESKY_PASSWORD")

        return self

    def set_credentials(self, email: str, password: str) -> None:
        """Set the credentials directly.

        Args:
            email: The Bluesky email
            password: The Bluesky password
        """
        self.email = email
        self.password = password

    def load_credentials_from_env(self) -> None:
        """Load credentials from environment variables."""
        self.email = os.getenv("BLUESKY_EMAIL")
        self.password = os.getenv("BLUESKY_PASSWORD")

    def are_valid(self) -> bool:
        """Check if the credentials are valid.

        Returns:
            bool: True if both email and password are set, False otherwise
        """
        return self.email is not None and self.password is not None
