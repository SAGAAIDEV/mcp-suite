"""Redis management for MCP Suite using a singleton pattern."""

import subprocess
import time
from typing import Optional, Tuple
from urllib.parse import urlparse

import redis
from loguru import logger

from src.config.env import REDIS
from src.mcp_suite.base.models.singleton import Singleton

from .utils import get_db_dir


class RedisManager(Singleton):
    """Singleton class to manage Redis server and client connections.

    This class provides methods to:
    1. Parse Redis URLs
    2. Launch a Redis server if not already running
    3. Connect to a Redis server
    4. Shutdown a Redis server that was launched by this manager
    5. Close Redis client connections

    All state is maintained in the singleton instance.
    """

    # Redis client connection
    client: Optional[redis.Redis] = None

    # Redis server process
    process: Optional[subprocess.Popen] = None

    # Whether Redis was launched by us
    launched_by_us: bool = False

    def parse_redis_url(self, url: str) -> Tuple[str, int, Optional[str], int]:
        """Parse Redis URL into connection parameters.

        Args:
            url: Redis URL string

        Returns:
            tuple: Host, port, password, and db number
        """
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        password = parsed.password

        # Extract DB number from path
        path = parsed.path
        db = 0
        if path and len(path) > 1:
            try:
                db = int(path[1:])
            except ValueError:
                logger.warning(f"Invalid DB number in Redis URL: {path[1:]}, using 0")

        return host, port, password, db

    def connect_to_redis(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        db: Optional[int] = None,
    ) -> Optional[redis.Redis]:
        """Connect to a Redis server.

        Args:
            host: Redis server hostname. Defaults to value from env config.
            port: Redis server port. Defaults to value from env config.
            password: Redis server password. Defaults to value from env config.
            db: Redis database number. Defaults to value from env config.

        Returns:
            Optional[redis.Redis]: Redis client instance or None if connection fails
        """
        # Parse Redis URL from environment config
        redis_host, redis_port, redis_password, redis_db = self.parse_redis_url(
            REDIS.URL
        )

        # Use provided values if specified, otherwise use values from config
        host = host or redis_host
        port = port or redis_port
        password = password or redis_password or "redispassword"
        db = db if db is not None else redis_db

        try:
            client = redis.Redis(
                host=host, port=port, password=password, db=db, decode_responses=True
            )
            # Test the connection
            client.ping()
            logger.info(f"Successfully connected to Redis at {host}:{port}")
            self.client = client
            return client
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return None

    def launch_redis_server(
        self,
        port: Optional[int] = None,
        password: Optional[str] = None,
        appendonly: bool = True,
        keyspace_events: str = "KEA",
    ) -> Tuple[bool, Optional[subprocess.Popen]]:
        """Launch a Redis server if it's not already running.

        Args:
            port: Redis server port. Defaults to value from env config.
            password: Redis server password. Defaults to value from env config.
            appendonly: Enable append-only file persistence. Defaults to True.
            keyspace_events: Keyspace notifications configuration. Defaults to "KEA".

        Returns:
            Tuple[bool, Optional[subprocess.Popen]]: Success status and process handle
        """
        # Parse Redis URL from environment config
        host, redis_port, redis_password, _ = self.parse_redis_url(REDIS.URL)

        # Use provided values if specified, otherwise use values from config
        port = port or redis_port
        password = password or redis_password or "redispassword"

        # Check if Redis is already running on the specified port
        try:
            client = redis.Redis(
                host=host, port=port, password=password, socket_connect_timeout=1
            )
            client.ping()
            logger.info(f"Redis server already running on port {port}")
            client.close()
            self.launched_by_us = False  # We didn't launch it
            return True, None
        except (redis.ConnectionError, redis.ResponseError):
            logger.info(f"No Redis server found on port {port}, launching new instance")

        # Prepare Redis server command
        cmd = [
            "redis-server",
            "--port",
            str(port),
            "--requirepass",
            password,
        ]

        if appendonly:
            cmd.extend(["--appendonly", "yes"])

        if keyspace_events:
            cmd.extend(["--notify-keyspace-events", keyspace_events])

        # Set working directory to the data directory
        db_dir = get_db_dir()
        cmd.extend(["--dir", str(db_dir)])

        try:
            # Launch Redis server as a subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Store the process in the instance
            self.process = process

            # Give Redis time to start
            time.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                logger.success(f"Successfully launched Redis server on port {port}")
                logger.info(f"Redis database files will be stored in {db_dir}")
                self.launched_by_us = True  # We launched it
                return True, process
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Redis server failed to start: {stderr}")
                self.process = None
                self.launched_by_us = False
                return False, None
        except Exception as e:
            logger.error(f"Failed to launch Redis server: {e}")
            self.launched_by_us = False
            return False, None

    def shutdown_redis_server(self):
        """Shutdown the Redis server if it was launched by us."""
        # Shutdown Redis server ONLY if we started it
        if self.launched_by_us and self.process is not None:
            try:
                logger.info("Shutting down Redis server that we launched")
                # Try graceful shutdown first using redis-cli
                if self.client is not None:
                    try:
                        self.client.shutdown(save=True)
                    except Exception as e:
                        logger.warning(f"Could not shutdown Redis via client: {e}")

                # Check if process is still running
                if self.process.poll() is None:
                    logger.info("Terminating Redis server process")
                    self.process.terminate()
                    # Give it some time to terminate gracefully
                    time.sleep(1)

                    # Force kill if still running
                    if self.process.poll() is None:
                        logger.warning(
                            "Redis server not responding to terminate, forcing kill"
                        )
                        self.process.kill()

                logger.success("Redis server shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down Redis server: {e}")

            # Reset the instance variables
            self.process = None
            self.launched_by_us = False

    def close_redis_connection(self):
        """Close the Redis client connection if it exists."""
        if self.client is not None:
            try:
                logger.info("Closing Redis client connection")
                self.client.close()
                self.client = None
            except Exception as e:
                logger.error(f"Error closing Redis client: {e}")

    def get_client(self) -> Optional[redis.Redis]:
        """Get the Redis client, connecting if necessary.

        Returns:
            Optional[redis.Redis]: Redis client instance or None if connection fails
        """
        if self.client is None:
            self.connect_to_redis()
        return self.client

    def ensure_redis_running(self) -> bool:
        """Ensure Redis is running, launching it if necessary.

        Returns:
            bool: True if Redis is running, False otherwise
        """
        try:
            # Try to connect first
            client = self.get_client()
            if client is not None:
                return True

            # If connection failed, try to launch
            success, _ = self.launch_redis_server()
            if success:
                # Connect to the server we just launched
                self.connect_to_redis()
                return True

            return False
        except Exception as e:
            logger.error(f"Error ensuring Redis is running: {e}")
            return False


# Create a global instance for easy access
redis_manager = RedisManager()
