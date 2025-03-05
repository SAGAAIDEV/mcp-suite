"""Tests for the BlueskyCredentials model."""

import os
from unittest import mock

import pytest

from src.mcp_suite.servers.bluesky_mcp_server.model.credentials import (
    BlueskyCredentials,
)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with mock.patch.dict(
        os.environ,
        {"BLUESKY_EMAIL": "test@example.com", "BLUESKY_PASSWORD": "password123"},
    ):
        yield


@pytest.fixture
def mock_empty_env_vars():
    """Mock empty environment variables for testing."""
    with mock.patch.dict(
        os.environ,
        {},
        clear=True,  # This clears all environment variables
    ):
        yield


def test_credentials_init():
    """Test that credentials can be initialized directly."""
    credentials = BlueskyCredentials(email="user@example.com", password="secret")
    assert credentials.email == "user@example.com"
    assert credentials.password == "secret"
    assert credentials.are_valid() is True


def test_credentials_empty(mock_empty_env_vars):
    """Test that empty credentials are not valid."""
    credentials = BlueskyCredentials()
    assert credentials.email is None
    assert credentials.password is None
    assert credentials.are_valid() is False


def test_set_credentials():
    """Test setting credentials directly."""
    credentials = BlueskyCredentials()
    credentials.set_credentials("user@example.com", "secret")
    assert credentials.email == "user@example.com"
    assert credentials.password == "secret"
    assert credentials.are_valid() is True


def test_load_credentials_from_env(mock_env_vars):
    """Test loading credentials from environment variables."""
    credentials = BlueskyCredentials()
    credentials.load_credentials_from_env()
    assert credentials.email == "test@example.com"
    assert credentials.password == "password123"
    assert credentials.are_valid() is True


def test_validate_credentials_from_env(mock_env_vars):
    """Test that credentials are validated from environment during initialization."""
    credentials = BlueskyCredentials()
    assert credentials.email == "test@example.com"
    assert credentials.password == "password123"
    assert credentials.are_valid() is True
