"""
Utility functions for the MCP suite project.

This module provides utility functions for test path conversion
and other helper methods used throughout the project.
"""

import os
from pathlib import Path
from typing import Optional


def source_to_test_path(source_path: str, test_type: str = "unit") -> str:
    """
    Convert a source file path to its corresponding test file path.

    Args:
        source_path: Path to the source file
        test_type: Type of test (unit, integration, etc.)

    Returns:
        Path to the corresponding test file

    Examples:
        >>> source_path = "src/mcp_suite/tools/testing/models.py"
        >>> source_to_test_path(source_path)
        'src/tests/unit/test_tools/test_testing/test_models.py'
    """
    # Normalize path
    source_path = os.path.normpath(source_path)

    # Split the path into components
    parts = Path(source_path).parts

    # Find where src is
    try:
        src_index = parts.index("src")
    except ValueError as exc:
        raise ValueError("Path does not contain 'src' directory") from exc

    # Check if next part is mcp_suite
    if len(parts) <= src_index + 1 or parts[src_index + 1] != "mcp_suite":
        raise ValueError("Path does not follow the expected format src/mcp_suite/...")

    # Create the new path parts
    new_parts = list(parts[: src_index + 1])  # Keep 'src'
    new_parts.append("tests")  # Add 'tests'
    new_parts.append(test_type)  # Add test type (unit, integration, etc.)

    # Add test_ prefix to remaining directories and files (skip mcp_suite)
    for part in parts[src_index + 2 :]:  # Skip src and mcp_suite
        if part.endswith(".py"):
            # Handle the filename
            filename = os.path.splitext(part)[0]  # Remove extension
            new_parts.append(f"test_{filename}.py")
        else:
            # Handle directories
            new_parts.append(f"test_{part}")

    # Join everything back together
    return os.path.join(*new_parts)


def create_test_file(
    source_path: str,
    test_type: str = "unit",
    create_dirs: bool = True,
) -> Optional[str]:
    """
    Create a test file for the given source file.

    Args:
        source_path: Path to the source file
        test_type: Type of test (unit, integration, etc.)
        create_dirs: Whether to create directories

    Returns:
        Path to the created test file or None if failed
    """
    try:
        test_path = source_to_test_path(source_path, test_type)

        # Create directories if needed
        if create_dirs:
            os.makedirs(os.path.dirname(test_path), exist_ok=True)

        # Skip if file already exists
        if os.path.exists(test_path):
            print(f"Test file already exists: {test_path}")
            return test_path

        # Create empty file
        with open(test_path, "w", encoding="utf-8"):
            pass

        print(f"Created test file: {test_path}")
        return test_path

    except (ValueError, OSError, IOError) as e:
        print(f"Error creating test file: {e}")
        return None
