"""
Constants for the development server.
"""

from enum import Enum
from pathlib import Path


class ReportPaths(Path, Enum):
    """Enum for report file paths."""

    @staticmethod
    def _get_git_root():
        """Find the git root directory by traversing up from the current file."""
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

    # Get git root once at module import time
    _GIT_ROOT = _get_git_root()

    # Use full absolute paths from git root
    PYTEST_RESULTS = _GIT_ROOT / "reports" / "pytest_results.json"
    FAILED_TESTS = _GIT_ROOT / "reports" / "failed_tests.json"
    COVERAGE = _GIT_ROOT / "reports" / "coverage.json"
    AUTOFLAKE = _GIT_ROOT / "reports" / "autoflake.json"
    FLAKE8 = _GIT_ROOT / "reports" / "flake8.json"
