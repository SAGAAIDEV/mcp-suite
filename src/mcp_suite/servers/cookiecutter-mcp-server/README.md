# MCP Server Cookiecutter Template

This is a Cookiecutter template for creating new MCP servers in the MCP Suite project.

## Using the Template

### With Cursor Rule (Recommended)

The easiest way to use this template is with the Cursor rule:

1. Open the Command Palette in Cursor (Cmd+Shift+P or Ctrl+Shift+P)
2. Type "Create MCP Server" and select the rule
3. Fill in the requested information:
   - MCP Server Name (e.g., "Blue Sky MCP Server")
   - MCP Server Slug (e.g., "bluesky_mcp_server")
   - MCP Server Description
   - Use FastAPI (yes/no)
   - Include CLI (yes/no)
   - Use Docker (yes/no)

### Manual Usage

You can also run Cookiecutter manually:

```bash
# Navigate to the mcp_suite directory
cd src/mcp_suite

# Run Cookiecutter with UV
uv run cookiecutter cookiecutter-mcp-server -o .
```

Or with specific parameters:

```bash
uv run cookiecutter cookiecutter-mcp-server -o . --no-input \
  project_name="Blue Sky MCP Server" \
  project_slug="bluesky_mcp_server" \
  project_short_description="A MCP server for Blue Sky integration" \
  use_fastapi=yes \
  include_cli=yes \
  use_docker=no
```

## Template Options

- **project_name**: The human-readable name of the project
- **project_slug**: The machine-friendly name of the project (auto-generated from project_name)
- **package_name**: The Python package name (same as project_slug)
- **project_short_description**: A brief description of the project
- **version**: The initial version number
- **author_name**: The name of the project author
- **author_email**: The email of the project author
- **python_version**: The minimum Python version required
- **use_docker**: Whether to include Docker configuration
- **use_fastapi**: Whether to include FastAPI setup
- **include_cli**: Whether to include command-line interface
- **open_source_license**: The license to use for the project

## Development

To modify this template, edit the files in the `cookiecutter-mcp-server` directory. The template uses Jinja2 syntax for variable substitution and conditional logic. 