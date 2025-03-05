"""Core module for MCP Suite."""

# mypy: ignore-errors


def main() -> str:
    """Run the main function.

    Returns:
        str: A greeting message
    """
    return "Hello from mcp-suite!"


if __name__ == "__main__":  # pragma: no cover
    print(main())
