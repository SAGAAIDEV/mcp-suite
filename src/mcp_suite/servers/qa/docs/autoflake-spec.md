# AutoFlake Feature Specification

## Overview
The AutoFlake feature will be a new tool in the MCP suite that automatically identifies and fixes unused imports and variables in Python code. This tool will help maintain clean, efficient code by removing unnecessary elements that can cause confusion and bloat.

**Note:** Unlike isort, which focuses on reordering and organizing imports, AutoFlake specifically targets the removal of unused imports and variables. These tools are complementary and could potentially be used together for comprehensive import management.

## Feature Requirements

1. **Run AutoFlake Analysis**: Execute AutoFlake on specified files or directories
2. **Generate Reports**: Create detailed JSON reports of findings
3. **Process Results**: Collect and organize all identified issues
4. **Iterative Issue Resolution**: Present issues one by one with clear instructions
5. **Automatic Fixing Option**: Provide capability to automatically fix issues when possible

## Implementation Components

### New Dependencies
- `autoflake` package
- `flake8` package with JSON formatter plugin for reporting

### New Files
- `src/mcp_suite/servers/dev/servers/autoflake.py` - Main server implementation
- `src/mcp_suite/servers/dev/service/autoflake_service.py` - Service for processing autoflake results

### Data Processing

The AutoFlake feature will directly process the JSON output from flake8, which already provides a well-structured format:

```json
[
  {
    "code": "F401",
    "filename": "src/module/example.py",
    "line_number": 3,
    "column_number": 1,
    "text": "'os' imported but unused",
    "physical_line": "import os"
  }
]
```

This structured output contains all necessary information:
- `code`: The error code (F401 for unused imports, F841 for unused variables)
- `filename`: Path to the file with the issue
- `line_number`: Line where the issue occurs
- `column_number`: Column position of the issue
- `text`: Description of the issue
- `physical_line`: The actual code with the issue

By directly using this JSON structure, we can avoid creating additional data models while still providing detailed information about each issue.

## Server Implementation

The AutoFlake server will follow the same pattern as the PyTest server, using FastMCP and the exception_handler decorator:

```python
# autoflake.py
from mcp.server.fastmcp import FastMCP
import subprocess
from pathlib import Path
import json
import time

from mcp_suite.servers.dev.utils.decorators import exception_handler
from ..utils.git_utils import get_git_root
from ..service.autoflake_service import process_autoflake_results
from src.mcp_suite.servers.dev import logger

mcp = FastMCP("autoflake")

@mcp.tool()
@exception_handler()
async def run_autoflake(file_path: str = ".", fix: bool = False):
    """Run autoflake analysis on specified files or directories.
    
    Args:
        file_path: Path to the file or directory to analyze (relative to git root)
                  Defaults to current directory if not specified
        fix: Boolean flag to automatically apply fixes (default: False)
    
    Returns:
        Status report with issue details and instructions for fixing
    """
    # Implementation details...
```

## Service Implementation

The AutoFlake service will process the results from flake8:

```python
# autoflake_service.py
def process_autoflake_results(
    input_file: Union[str, Path] = "./reports/autoflake.json"
) -> dict:
    """
    Process autoflake results JSON and extract issues.
    
    Args:
        input_file: Path to the autoflake results JSON file
        
    Returns:
        Dictionary containing summary and issues
    """
    # Implementation details...
```

## Tool Interface

```
run_autoflake(file_path: str, fix: bool = False)
```

The implementation will use a two-step process:

1. First, run autoflake to fix issues automatically (if fix=True):

```bash
uv run autoflake --remove-all-unused-imports --remove-unused-variables --recursive --in-place --pyproject-toml ./pyproject.toml
```

2. Then, use Flake8 with JSON output to generate reports on any remaining issues:

```bash
uv run flake8 --format=json --output-file=./reports/autoflake.json --select=F401,F841 {file_path} --pyproject-toml ./pyproject.toml
```

These commands:
- First attempt to automatically fix unused imports and variables
- Read configuration from pyproject.toml using the --pyproject-toml flag
- Then generate a structured JSON report of any remaining issues
- Can be configured to scan specific directories
- Select only unused imports (F401) and unused variables (F841) for reporting
- Use `uv run` to ensure consistent environment management

**Parameters:**
- `file_path`: Path to the file or directory to analyze (relative to git root)
- `fix`: Boolean flag to automatically apply fixes (default: False)

**Returns:**
- Status report with issue details and instructions for fixing

## Execution Flow

1. The `run_autoflake` function is called with a file path and fix option
2. The function finds the git root directory using `get_git_root()`
3. If no specific file path is provided (or if it's empty), the tool defaults to using the current directory (".") and runs over all Python files
4. If `fix=True`, it runs autoflake with the `--in-place` option to fix issues
5. It then runs flake8 to generate a JSON report of any remaining issues
6. The JSON report is processed by `process_autoflake_results()`
7. If issues are found, the first issue is returned with instructions
8. If no issues are found, a success message is returned

## User Workflow

1. User calls the `run_autoflake` tool with a target file or directory
2. Tool executes AutoFlake and generates a report
3. If issues are found:
   - The first issue is presented with detailed information
   - Instructions for fixing the issue are provided
   - User makes the necessary changes
   - User runs the tool again to check for additional issues
4. Process continues until all issues are resolved
5. Tool confirms when code is clean

## Example Output

For issues found:
```json
{
  "Status": "Issues Found",
  "Issue": {
    "file_path": "src/module/example.py",
    "line_number": 3,
    "column": 1,
    "issue_type": "unused_import",
    "message": "'os' imported but unused",
    "code": "F401",
    "physical_line": "import os"
  },
  "Instructions": "Let's fix the issue type in the file_path at the line number. After fixing this issue, run the run_autoflake tool again to check for more issues."
}
```

For success:
```json
{
  "Status": "Success",
  "Message": "Great job! Your code is clean with no unused imports or variables.",
  "Instructions": "Your code is looking great! You might want to run other code quality tools like isort or black next to ensure your code is well-formatted."
}
```

## Integration with Existing Tools

The AutoFlake tool follows the same pattern as the existing PyTest and coverage tools:
- Uses the same exception handling mechanism with the `@exception_handler()` decorator
- Generates reports in a similar JSON format
- Processes results using a dedicated service module
- Presents issues one at a time with clear instructions
- Provides a consistent user experience with helpful messages

## Future Enhancements

1. Support for custom AutoFlake configurations
2. Integration with other code quality tools (isort, black, etc.)
3. Batch mode for fixing multiple issues at once
4. Detailed statistics on code quality improvements over time
5. Support for ignoring specific files or directories
6. Configuration options for different levels of strictness
