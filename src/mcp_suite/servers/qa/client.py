"""Client for the QA server.

This module provides a client for interacting with the QA server,
allowing users to set log file paths and run various QA tools.
"""

from pathlib import Path
from typing import Dict, Union

import httpx


class QAClient:
    """Client for the QA server.

    This client provides methods for interacting with the QA server,
    including setting log file paths and running various QA tools.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the QA client.

        Args:
            base_url: Base URL of the QA server. Defaults to "http://localhost:8000".
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=60.0)

    def set_log_file(self, log_path: Union[str, Path]) -> Dict:
        """Set a new log file path.

        Args:
            log_path: Path to the new log file. Can be a string or Path object.

        Returns:
            Dict: Response from the server.

        Raises:
            httpx.HTTPStatusError: If the server returns an error.
        """
        # Convert Path to string if needed
        if isinstance(log_path, Path):
            log_path = str(log_path)

        # Make the request
        response = self.client.post(
            f"{self.base_url}/set_log_file", json={"log_path": log_path}
        )
        response.raise_for_status()

        return response.json()

    def get_log_file(self) -> Dict:
        """Get the current log file path.

        Returns:
            Dict: Response from the server with the current log file path.

        Raises:
            httpx.HTTPStatusError: If the server returns an error.
        """
        response = self.client.get(f"{self.base_url}/get_log_file")
        response.raise_for_status()

        return response.json()


def main():  # pragma: no cover
    """Command-line interface for the QA client."""
    import argparse

    # Create argument parser
    parser = argparse.ArgumentParser(description="QA Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Set log file parser
    set_log_parser = subparsers.add_parser("set-log", help="Set a new log file")
    set_log_parser.add_argument("log_path", help="Path to the new log file")

    # Get log file parser
    _ = subparsers.add_parser("get-log", help="Get the current log file")

    # Server URL argument for all commands
    parser.add_argument(
        "--server", default="http://localhost:8000", help="URL of the QA server"
    )

    # Parse arguments
    args = parser.parse_args()

    # Create client
    client = QAClient(base_url=args.server)

    # Run command
    if args.command == "set-log":
        response = client.set_log_file(args.log_path)
        print(f"Log file set to: {response['log_path']}")
    elif args.command == "get-log":
        response = client.get_log_file()
        print(f"Current log file: {response['log_path']}")
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
