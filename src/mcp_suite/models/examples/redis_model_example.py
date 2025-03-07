"""
Example usage of the RedisModel class.

This module demonstrates how to create and use Redis-backed models.
"""

import asyncio
from datetime import UTC, datetime
from typing import List, Optional

from loguru import logger

from mcp_suite.models.redis_model import RedisModel


class User(RedisModel):
    """
    Example user model using RedisModel.

    This model demonstrates how to create a custom model that extends RedisModel.
    """

    email: str
    is_active: bool = True
    last_login: Optional[datetime] = None
    roles: List[str] = []


async def main():
    """Example usage of the User model."""
    try:
        # Create a new user
        user = User(
            name="John Doe",
            email="john.doe@example.com",
            description="Example user",
            roles=["user", "admin"],
        )
        logger.info(f"Created user: {user}")

        # Save the user to Redis
        success = await user.save_to_redis()
        if success:
            logger.info(f"User saved to Redis with ID: {user.id}")
        else:
            logger.error("Failed to save user to Redis")
            return

        # Load the user from Redis
        loaded_user = await User.load_from_redis(user.id)
        if loaded_user:
            logger.info(f"Loaded user from Redis: {loaded_user}")
        else:
            logger.error(f"Failed to load user with ID: {user.id}")
            return

        # Check if the user exists in Redis
        exists = await User.exists_in_redis(user.id)
        logger.info(f"User exists in Redis: {exists}")

        # Update the user
        loaded_user.last_login = datetime.now(UTC)
        loaded_user.roles.append("moderator")
        await loaded_user.save_to_redis()
        logger.info(f"Updated user: {loaded_user}")

        # Get all users from Redis
        all_users = await User.get_all_from_redis()
        logger.info(f"Found {len(all_users)} users in Redis")

        # Delete the user from Redis
        success = await loaded_user.delete_from_redis()
        if success:
            logger.info(f"Deleted user with ID: {loaded_user.id}")
        else:
            logger.error(f"Failed to delete user with ID: {loaded_user.id}")

        # Verify the user no longer exists
        exists = await User.exists_in_redis(user.id)
        logger.info(f"User exists in Redis after deletion: {exists}")

    except Exception as e:
        logger.error(f"Error in example: {e}")


if __name__ == "__main__":  # pragma: no cover
    # Run the example
    asyncio.run(main())
