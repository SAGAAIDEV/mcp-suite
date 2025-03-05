"""Tests for the Bluesky MCP server."""

import base64
from unittest import mock

import pytest

from src.mcp_suite.servers.bluesky_mcp_server.server import bluesky


@pytest.fixture
def mock_bluesky_service():
    """Mock the BlueskyService."""
    with mock.patch(
        "src.mcp_suite.servers.bluesky_mcp_server.server.bluesky.bluesky_service"
    ) as mock_service:
        mock_service.post_text.return_value = "at://test/post/123"
        mock_service.post_with_image.return_value = "at://test/post/456"
        yield mock_service


@pytest.mark.asyncio
async def test_post_text(mock_bluesky_service):
    """Test the post_text MCP tool."""
    result = await bluesky.post_text("Hello, world!")

    mock_bluesky_service.post_text.assert_called_once_with("Hello, world!")
    assert "Successfully posted to Bluesky" in result
    assert "at://test/post/123" in result


@pytest.mark.asyncio
async def test_post_text_error(mock_bluesky_service):
    """Test the post_text MCP tool with an error."""
    mock_bluesky_service.post_text.side_effect = Exception("Test error")

    result = await bluesky.post_text("Hello, world!")

    mock_bluesky_service.post_text.assert_called_once_with("Hello, world!")
    assert "Failed to post to Bluesky" in result
    assert "Test error" in result


@pytest.mark.asyncio
async def test_post_with_image(mock_bluesky_service):
    """Test the post_with_image MCP tool."""
    # Create a simple base64 encoded image
    image_data = b"fake_image_data"
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    result = await bluesky.post_with_image(
        "Hello with image!", image_base64, "Alt text"
    )

    mock_bluesky_service.post_with_image.assert_called_once_with(
        "Hello with image!", image_data, "Alt text"
    )
    assert "Successfully posted image and text to Bluesky" in result
    assert "at://test/post/456" in result


@pytest.mark.asyncio
async def test_post_with_image_error(mock_bluesky_service):
    """Test the post_with_image MCP tool with an error."""
    # Create a simple base64 encoded image
    image_data = b"fake_image_data"
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    mock_bluesky_service.post_with_image.side_effect = Exception("Test error")

    result = await bluesky.post_with_image(
        "Hello with image!", image_base64, "Alt text"
    )

    mock_bluesky_service.post_with_image.assert_called_once_with(
        "Hello with image!", image_data, "Alt text"
    )
    assert "Failed to post to Bluesky" in result
    assert "Test error" in result
