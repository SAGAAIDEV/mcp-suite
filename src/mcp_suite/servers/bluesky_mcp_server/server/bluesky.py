"""Bluesky MCP Service

A Bluesky social media posting service using the ATProto SDK.
It provides functionality to create text posts and image+text posts on Bluesky.

The service is implemented as a FastMCP server that exposes two tools:
- post_text: Creates a text-only post on Bluesky
- post_with_image: Creates a post with both text and an image

Dependencies:
    - atproto: For Bluesky API integration
    - mcp: For FastMCP server implementation
"""

import base64
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from ..model.service import BlueskyService

# Load environment variables
load_dotenv()

# Initialize the FastMCP server
mcp = FastMCP("bluesky")

# Initialize Bluesky service with credentials from environment
bluesky_service = BlueskyService()


# For execution order: scheduled_tool runs first, then mcp.tool
# In Python, decorators are executed from bottom to top
@mcp.tool(name="post_text")
# @scheduled_tool
async def post_text(text: str) -> str:
    """Post text content to Bluesky.

    Args:
        text: The text content to post, it should be under 300 characters
              and have hash tags.

    Returns:
        A success message with the post URI

        datetime: Optional[str] - When provided, schedules the function to run
                 at the specified time. Format: 'YYYY-MM-DDTHH:MM:SS'
                 Example: '2023-12-31T23:59:59'
                 for December 31, 2023 at 11:59:59 PM
    """
    try:
        post_uri = bluesky_service.post_text(text)
        return f"Successfully posted to Bluesky! Post URI: {post_uri}"
    except Exception as e:
        return f"Failed to post to Bluesky: {str(e)}"


# For execution order: scheduled_tool runs first, then mcp.tool
# In Python, decorators are executed from bottom to top
@mcp.tool(
    name="post_with_image",
    description="Create a post with text and an image on Bluesky",
)
async def post_with_image(
    text: str,
    image_base64: str,
    alt_text: Optional[str] = None,
) -> str:
    """Post text content with an image to Bluesky.

    Args:
        text: The text content to post
        image_base64: Base64 encoded image data
        alt_text: Optional alternative text for the image

    Returns:
        A success message with the post URI
    """
    try:
        # Decode base64 image
        image_data = base64.b64decode(image_base64)

        # Post with image
        post_uri = bluesky_service.post_with_image(text, image_data, alt_text)

        return f"Successfully posted image and text to Bluesky!\
              Post URI: {post_uri}"
    except Exception as e:
        return f"Failed to post to Bluesky: {str(e)}"


if __name__ == "__main__":  # pragma: no cover
    mcp.run(transport="stdio")
