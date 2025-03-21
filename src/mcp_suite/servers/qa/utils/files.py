from pathlib import Path


def is_valid_python_path(path: str) -> bool:
    """
    Check if a path is a valid Python file.

    Args:
        path: The file path to check

    Returns:
        bool: True if the path exists and is a Python file, False otherwise
    """
    try:
        # Convert to Path object for easier handling
        path_obj = Path(path)

        # Check if the file exists
        if not path_obj.exists():
            return False

        # Check if it's a file (not a directory)
        if not path_obj.is_file():
            return False

        # Check if it has a .py extension
        if not path_obj.suffix == ".py":
            return False

        # Try to open and read the file to ensure it's accessible
        with open(path_obj, "r", encoding="utf-8") as f:
            # Just read a small part to verify it's readable
            f.read(1)

        return True
    except (IOError, OSError, UnicodeDecodeError):
        # Handle file access errors or encoding issues
        return False
