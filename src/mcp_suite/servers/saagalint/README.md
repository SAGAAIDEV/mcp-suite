# SaagaLint

A comprehensive linting and testing tool for Python projects.

## Overview

SaagaLint provides a set of tools for running tests, checking code coverage, and performing static analysis on Python code. It integrates with pytest, coverage, and various linting tools to provide a unified interface for code quality checks.

## Features

- **Pytest Integration**: Run tests and analyze results
- **Coverage Analysis**: Check code coverage and identify untested code
- **Autoflake Integration**: Detect and fix unused imports and variables
- **Component-specific Logging**: Each tool writes to its own log file
- **Google Fire CLI**: Easy command-line interface with multiple options
- **MCP Server Integration**: Run as an MCP server with stdio or SSE transport

## Directory Structure

```
saagalint/
├── __init__.py          # Package initialization and main logger setup
├── __main__.py          # Entry point for the package
├── README.md            # This file
├── logs/                # Directory for log files
├── tools/               # Tool implementations
│   ├── __init__.py      # Package initialization
│   ├── pytest_tool.py   # Pytest tool implementation
│   ├── coverage_tool.py # Coverage tool implementation
│   ├── autoflake_tool.py # Autoflake tool implementation
│   └── register_tools.py # Tool registration
├── service/             # Service implementations
├── utils/               # Utility functions
│   ├── decorators.py    # Decorator utilities
│   ├── git_utils.py     # Git utilities
│   └── logging_utils.py # Logging utilities
└── config/              # Configuration files
```

## Usage

### Command Line

```bash
# Run with default settings (stdio transport)
python -m src.mcp_suite.servers.saagalint

# Run with SSE transport
python -m src.mcp_suite.servers.saagalint --transport=sse

# Run with SSE transport on a specific host and port
python -m src.mcp_suite.servers.saagalint --transport=sse --host=0.0.0.0 --port=8082

# Run with debug mode enabled
python -m src.mcp_suite.servers.saagalint --debug=True
```

### Available Tools

#### run_pytest

Run pytest tests and analyze results.

```python
await run_pytest("src/mcp_suite/base/redis_db/tests/test_redis_manager.py")
# Or run all tests
await run_pytest(".")
```

#### run_coverage

Check code coverage and identify untested code.

```python
await run_coverage("src/mcp_suite/base/redis_db/redis_manager.py")
# Or check all coverage
await run_coverage(None)
```

#### run_autoflake

Detect and fix unused imports and variables.

```python
# Run with automatic fixes (default)
await run_autoflake("src/mcp_suite/base/redis_db/redis_manager.py")
# Run without automatic fixes
await run_autoflake("src/mcp_suite/base/redis_db/redis_manager.py", fix=False)
```

## Logging

SaagaLint uses a component-based logging system. Each component writes to its own log file in the `logs/` directory:

- `saagalint.log`: Main log file
- `pytest.log`: Pytest tool log file
- `coverage.log`: Coverage tool log file
- `autoflake.log`: Autoflake tool log file

Log files are automatically rotated when they reach 10 MB in size.

## Development

### Adding a New Tool

1. Create a new file in the `tools/` directory
2. Implement the tool function with the `@exception_handler()` decorator
3. Use component-specific logging
4. Register the tool in `register_tools.py`

Example:

```python
# tools/my_tool.py
from mcp_suite.servers.saagalint import logger as main_logger
from mcp_suite.servers.saagalint.utils.decorators import exception_handler
from mcp_suite.servers.saagalint.utils.logging_utils import get_component_logger

# Get a component-specific logger
logger = get_component_logger("my_tool")

@exception_handler()
async def run_my_tool(param1, param2=None):
    """
    My tool description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        dict: Results and instructions
    """
    logger.info(f"Running my tool with {param1}, {param2}")
    main_logger.info(f"Running my tool with {param1}, {param2}")
    
    # Tool implementation
    
    return {
        "Status": "Success",
        "Message": "Tool ran successfully",
        "Instructions": "Next steps..."
    }
```

Then register it in `register_tools.py`:

```python
from mcp_suite.servers.saagalint.tools.my_tool import run_my_tool

def register_tools(mcp):
    # ... existing registrations
    
    # Register my tool
    logger.debug("Registering run_my_tool tool")
    mcp.tool()(run_my_tool)
```

## Troubleshooting

If you encounter issues:

1. Check the component-specific log file in the `logs/` directory
2. Enable debug mode: `python -m src.mcp_suite.servers.saagalint --debug=True`
3. Check the main log file for server-level issues 