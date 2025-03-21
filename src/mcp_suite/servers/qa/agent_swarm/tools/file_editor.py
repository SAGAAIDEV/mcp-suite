import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from langchain_core.tools import tool

from mcp_suite.servers.qa.utils.git_utils import get_git_root

"""A class that provides tools for editing files."""


@tool
def read_file(file_path: str) -> str:
    """
    Read the contents of a file.

    Args:
        file_path: The path to the file to read

    Returns:
        The contents of the file as a string
    """
    try:
        git_root = get_git_root()
        return (git_root / Path(file_path)).resolve().read_text()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_to_file(file_path: str, content: str) -> str:
    """
    Write content to a file, overwriting any existing content.

    Args:
        file_path: The path to the file to write to
        content: The content to write to the file

    Returns:
        A message indicating success or failure
    """
    try:
        # Create directory if it doesn't exist
        git_root = get_git_root()
        path = (git_root / Path(file_path)).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"


@tool
def append_to_file(file_path: str, content: str) -> str:
    """
    Append content to a file.

    Args:
        file_path: The path to the file to append to
        content: The content to append to the file

    Returns:
        A message indicating success or failure
    """
    try:
        # Create directory if it doesn't exist
        git_root = get_git_root()
        path = (git_root / Path(file_path)).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("a") as file:
            file.write(content)
        return f"Successfully appended to {path}"
    except Exception as e:
        return f"Error appending to file: {str(e)}"


@tool
def replace_in_file(file_path: str, search_text: str, replace_text: str) -> str:
    """
    Replace text in a file.

    Args:
        file_path: The path to the file
        search_text: The text to search for
        replace_text: The text to replace it with

    Returns:
        A message indicating success or failure and how many replacements were made
    """
    try:
        git_root = get_git_root()
        path = (git_root / Path(file_path)).resolve()
        content = path.read_text()

        # Count occurrences before replacement
        count = content.count(search_text)

        if count == 0:
            return f"No occurrences of '{search_text}' found in {path}"

        # Perform replacement
        new_content = content.replace(search_text, replace_text)

        path.write_text(new_content)

        return (
            f"Successfully replaced {count} occurrence(s) of '{search_text}' in {path}"
        )
    except Exception as e:
        return f"Error replacing text in file: {str(e)}"


@tool
def get_python_files_tree(directory: str = "") -> str:
    """
    Get a tree representation of Python files in the repository.

    Args:
        directory: Optional subdirectory to start from (relative to git root)
                  If empty, starts from git root

    Returns:
        A string representation of the tree structure with Python files only
    """
    try:
        git_root = get_git_root()
        start_dir = git_root

        if directory:
            start_dir = (git_root / directory).resolve()
            if not start_dir.exists() or not start_dir.is_dir():
                return (
                    f"Error: Directory '{directory}' does not exist "
                    "or is not a directory"
                )

        tree_output = []
        _build_python_tree(start_dir, git_root, "", tree_output, is_root=True)

        return "\n".join(tree_output)
    except Exception as e:
        return f"Error generating Python files tree: {str(e)}"


@tool
def execute_python_code(code: str, input_data: str = "") -> str:
    """
    Write and execute a Python program to find patterns or solve complex problems.

    This tool is useful when the agent needs to:
    - Process large amounts of data
    - Find complex patterns
    - Perform calculations
    - Test algorithms

    Args:
        code: The Python code to execute
        input_data: Optional input data to pass to the program via stdin

    Returns:
        The output of the executed program (stdout and stderr)
    """
    try:
        # Create a temporary directory for the script
        temp_dir = tempfile.mkdtemp(prefix="agent_script_")

        # Generate a unique filename
        script_name = f"agent_script_{uuid.uuid4().hex}.py"
        script_path = os.path.join(temp_dir, script_name)

        # Write the code to the temporary file
        with open(script_path, "w") as f:
            f.write(code)

        # Execute the script
        process = subprocess.run(
            ["python", script_path],
            input=input_data.encode() if input_data else None,
            capture_output=True,
            text=True,
            timeout=30,  # Set a timeout to prevent infinite loops
        )

        # Collect output
        output = []
        if process.stdout:
            output.append("=== STDOUT ===")
            output.append(process.stdout)

        if process.stderr:
            output.append("=== STDERR ===")
            output.append(process.stderr)

        if process.returncode != 0:
            output.append(f"=== PROCESS EXITED WITH CODE {process.returncode} ===")

        # Clean up
        try:
            os.remove(script_path)
            os.rmdir(temp_dir)
        except Exception as e:
            output.append(f"Warning: Failed to clean up temporary files: {str(e)}")

        return "\n".join(output)
    except subprocess.TimeoutExpired:
        return "Error: Script execution timed out (30 seconds limit)"
    except Exception as e:
        return f"Error executing Python code: {str(e)}"


def _build_python_tree(
    path: Path, git_root: Path, prefix: str, output: list, is_root: bool = False
):
    """
    Recursively build a tree representation of Python files.

    Args:
        path: Current directory path
        git_root: Git repository root path
        prefix: Prefix for the current line (for formatting)
        output: List to append output lines to
        is_root: Whether this is the root directory
    """
    if is_root:
        rel_path = path.relative_to(git_root)
        dir_name = str(rel_path) if str(rel_path) != "." else git_root.name
        output.append(f"{dir_name}/")
        new_prefix = "├── "
    else:
        dir_name = path.name
        output.append(f"{prefix}{dir_name}/")
        new_prefix = prefix.replace("├── ", "│   ").replace("└── ", "    ") + "├── "

    # Get all items in the directory
    items = list(path.iterdir())

    # Filter and sort: directories first, then Python files
    dirs = sorted([p for p in items if p.is_dir() and not p.name.startswith(".")])
    py_files = sorted([p for p in items if p.is_file() and p.suffix == ".py"])

    # Process all items
    for i, item in enumerate(dirs + py_files):
        is_last = i == len(dirs) + len(py_files) - 1
        current_prefix = new_prefix.replace("├── ", "└── ") if is_last else new_prefix

        if item.is_dir():
            # Check if directory contains any Python files (recursively)
            has_py_files = any(f.suffix == ".py" for f in item.glob("**/*.py"))
            if has_py_files:
                _build_python_tree(item, git_root, current_prefix, output)
        elif item.suffix == ".py":
            output.append(f"{current_prefix}{item.name}")


@tool
def reflect():
    """
    To be called when all errors are dealt with.
    """
    return (
        "read src/agents/tools/file_editor.py and make suggestions of how it could "
        "improve from your experiences this run. Write a file in the same directory "
        "for suggestions for review. After you are done."
    )
