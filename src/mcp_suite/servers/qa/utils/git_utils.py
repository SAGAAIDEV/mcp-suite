"""Git utility functions for the pytest server."""

from pathlib import Path

# Bind component to logger


def get_git_root():
    """
    Find the git root directory by traversing up from the current file.

    Returns:
        Path: The path to the git root directory.

    Raises:
        FileNotFoundError: If the git root directory cannot be found.
    """

    current_dir = Path(__file__).resolve().parent
    git_root = None

    # Navigate up until we find .git directory
    check_dir = current_dir
    while check_dir != check_dir.parent:
        if (check_dir / ".git").exists():
            git_root = check_dir

            break
        check_dir = check_dir.parent

    if git_root is None:
        error_msg = "Git repository root not found"

        raise FileNotFoundError(error_msg)

    return git_root
