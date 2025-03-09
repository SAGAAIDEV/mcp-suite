# MCP Suite Module

## Module Objective

The `mcp_suite` module serves as the core implementation of the MCP Suite application, a system tray application that manages Model Context Protocol (MCP) servers. This module provides the foundation for:

- Managing the system tray application interface
- Handling Redis-based state management
- Coordinating MCP server lifecycle management
- Processing authentication workflows
- Integrating with Docker for container management

## Installation Guide

### Prerequisites

- Python 3.13.0 or higher
- Docker installed and running
- Redis (optional, can be launched by the application)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/mcp-suite.git
   cd mcp-suite
   ```

2. Install the package with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Run the application:
   ```bash
   python -m mcp_suite
   ```

### Environment Configuration

The application can be configured via environment variables or a `.env` file:

- `REDIS_URL`: URL to connect to Redis (default: `redis://localhost:6379/0`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `DATA_DIR`: Directory for persistent data storage (default: `~/.mcp-suite`)

## Release Notes

### Version 0.1.0 (March 2023)

Initial alpha release of the MCP Suite module.

**Features:**
- Basic system tray application interface
- Redis-based state management
- Foundation for MCP server management

**Models/Libraries Used:**
- PyQt6/PySide6 for UI components
- Redis for state management
- Pydantic V2 for data modeling
- FastMCP (MCP extension of FastAPI) for server implementations

**Known Limitations:**
- Limited MCP server implementations
- Basic authentication workflows only
- Desktop application support limited to basic operations

### Future Roadmap

- Expand available MCP servers
- Enhance authentication management
- Improve Docker integration
- Add support for custom MCP server configurations