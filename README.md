# MCP Suite

## Overview

MCP Suite is a comprehensive system tray application that manages a collection of Model Context Protocol (MCP) servers, designed to empower AI agents with seamless access to a wide range of external services and APIs. By providing a standardized interface for LLMs to interact with various tools and platforms, MCP Suite bridges the gap between AI capabilities and real-world applications.

## Vision

Our vision is to create an ecosystem where AI agents can effortlessly extend their capabilities through a unified protocol, enabling them to access, manipulate, and leverage external services as naturally as they process text. MCP Suite aims to be the definitive toolkit that transforms LLMs from isolated text processors into connected agents that can take meaningful actions in the digital world.

## Key Features

- **System Tray Application**: Lightweight, always-accessible interface for managing MCP servers
- **Service Management**: One-click activation/deactivation of individual MCP servers
- **Authentication Management**: Simplified authentication workflows through a unified interface
- **Docker Integration**: Transparent management of the underlying Docker infrastructure
- **Redis-based State Management**: Persistent storage of service state and configuration
- **Cross-Platform Support**: Works on Windows, macOS, and Linux

## MCP Server Collection

MCP Suite provides a growing library of pre-configured MCP servers for popular services and platforms, including:

### Narrative and Communication Tools
- **Creative Tools**: Midjourney, DALL-E, Stable Diffusion
- **Social Media**: Twitter, LinkedIn, Instagram, BlueSky, TikTok, YouTube
- **Media Creation**: GStreamer, HeyGen

### Organizational Tools
- **Productivity Tools**: Google Workspace, Microsoft Office, Atlassian Suite
- **Talent Database**: Upwork, Custom, Athena

### Financial Tools
- **Financial Tools**: Bitcoin, Lightning Network, TapRoot Assets

### Development Tools
- **Development Tools**: Jira, Log Reader, Git, Debugger
- **Cloud Services**: AWS, GCP, Azure
- **Communication Platforms**: Slack, Discord, Email services
- **Knowledge Bases**: Notion, Confluence, Wikipedia, Google, Travily

### Logistic Tools
- **Location Tools**: Google Maps, Google Places

## Technology Stack

- **Programming Languages**: Python 3.9+
- **UI Frameworks**: PyQt6/PySide6, Qt QML
- **State Management**: Redis, pydantic-redis
- **Data Modeling**: Pydantic V2
- **API Development**: FastMCP (MCP-specific extension of FastAPI)
- **Task Management**: Celery, Flower
- **Testing**: pytest, pytest-cov, pytest-mock, hypothesis
- **Code Quality**: flake8, black, mypy, isort

## System Architecture

The MCP Suite follows a modular architecture with the following core components:

1. **System Tray Application**: The entry point that provides quick access to MCP servers and configuration
2. **Redis Server**: Stores service state, configuration, and enables communication between components
3. **Docker Manager**: Handles container lifecycle for MCP servers
4. **Service Manager**: Coordinates the operation of MCP servers
5. **Configuration UI**: Provides a user interface for managing settings and accounts
6. **MCP Servers**: Individual servers that provide specific functionality through the MCP protocol

## Documentation

For more detailed information, please refer to the following documentation:

- [Vision Statement](docs/vision_statement.md)
- [System Architecture](docs/system_architecture.md)
- [Technical Requirements](docs/technical_requirements.md)
- [Technology Stack](docs/technology_stack.md)
- [User Stories](docs/user_stories.md)
- [Sprint Planning](docs/sprint_planning_jira.md)
- [Development Plan](docs/sprint_development_plan.md)

## Getting Started

[Installation and setup instructions will be added here]

## Contributing

[Contribution guidelines will be added here]

## License

[License information will be added here]

## Testing

uv run python -m pytest . --cov=src/ --cov-report=term-missing 
