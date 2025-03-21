import json
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, List

from mcp_suite.servers.qa.utils.git_utils import get_git_root


def run_pylint_on_file(file_path: str) -> Dict[str, Any]:
    """Run pylint on a single file and return the results as a dictionary."""
    try:
        result = subprocess.run(
            ["uv", "run", "pylint", "--output-format=json", file_path],
            capture_output=True,
            cwd=get_git_root(),
            text=True,
            check=False,
        )

        # Parse the JSON output
        if result.stdout.strip():
            pylint_results = json.loads(result.stdout)
        else:
            pylint_results = []

        # process here
        # call agent-swarm here

        return {
            "file": file_path,
            "issues_count": len(pylint_results),
            "success": True,
            "results": pylint_results,
        }
    except Exception as e:
        return {
            "file": file_path,
            "issues_count": 0,
            "success": False,
            "error": str(e),
        }


def run_pylint_parallel(
    files_or_dirs: List[str], max_workers: int = 4
) -> List[Dict[str, Any]]:
    """
    Run pylint on multiple files or directories in parallel.

    Args:
        files_or_dirs: List of file or directory paths
        max_workers: Maximum number of parallel processes

    Returns:
        List of dictionaries with results for each file
    """
    # Expand directories to individual Python files
    python_files = []
    for path in files_or_dirs:
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):
                        python_files.append(os.path.join(root, file))
        elif path.endswith(".py"):
            python_files.append(path)

    # Run pylint in parallel
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(run_pylint_on_file, file): file for file in python_files
        }
        for future in future_to_file:
            results.append(future.result())

    print(f"Processed {len(python_files)} files.")
    print(f"Files with issues: {sum(1 for r in results if r['issues_count'] > 0)}")

    return results


if __name__ == "__main__":  # pragma: no cover
    # Example usage
    print("Running")
    paths_to_check = ["src/", "tests/"]  # Add your paths here
    run_pylint_parallel(paths_to_check, max_workers=8)
