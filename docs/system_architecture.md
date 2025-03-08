# MCP Suite - System Architecture

This document outlines the system architecture for the MCP Suite, describing how the various components interact and function together. This architecture implements the requirements specified in the [Technical Requirements](technical_requirements.md) document.

## Overview

The MCP Suite is designed as a system tray application that manages and provides access to multiple MCP servers. The architecture follows a modular approach with Redis for state management, Docker for containerization, and a dynamic service discovery mechanism.

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Suite System                        │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │ System Tray │    │ Config UI   │    │ Service Manager │  │
│  │ Application │◄───┤ Window      │◄───┤                 │  │
│  └─────┬───────┘    └─────────────┘    └────────┬────────┘  │
│        │                                        │           │
│        ▼                                        ▼           │
│  ┌─────────────┐                        ┌─────────────────┐ │
│  │ Docker      │                        │ Redis Server    │ │
│  │ Manager     │                        │ (State Storage) │ │
│  └─────┬───────┘                        └────────┬────────┘ │
│        │                                        │           │
│        └────────────────┬─────────────────────┬┘           │
│                         │                     │             │
│                         ▼                     ▼             │
│  ┌─────────────┐  ┌─────────────┐      ┌─────────────────┐ │
│  │ MCP Server 1│  │ MCP Server 2│  ... │ MCP Server N    │ │
│  └─────────────┘  └─────────────┘      └─────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. System Tray Application

The entry point of the MCP Suite is a system tray application that:
- Launches on system startup
- Provides quick access to MCP servers and configuration
- Displays status indicators for services
- Offers menu options for common operations

### 2. Redis Server

A Redis instance runs alongside the application to:
- Store service state and configuration
- Maintain credential information securely
- Enable persistence across application restarts
- Facilitate communication between components
- Support Celery task queue operations

### 3. Service Manager

The Service Manager is responsible for:
- Dynamically discovering available services
- Loading service configurations from Redis
- Managing service lifecycles
- Handling credential requirements
- Providing a unified interface for the UI components

### 4. Configuration UI

A configuration window that:
- Allows users to set credentials for services
- Provides service-specific configuration options
- Displays service status and information
- Scales dynamically as new services are added

### 5. Docker Manager

Handles Docker-related operations:
- Starting and stopping MCP server containers
- Monitoring container health
- Managing Docker Compose configurations
- Handling volume and network settings

### 6. MCP Servers

Individual service containers that:
- Implement specific functionality
- Inherit from a base service class
- Store state in Redis when needed
- Expose APIs for interaction

## Service Architecture

### Base Service Class

All MCP services inherit from a base service class that provides:

```
┌─────────────────────────────────────┐
│           BaseService               │
├─────────────────────────────────────┤
│ - service_id: str                   │
│ - service_name: str                 │
│ - accounts: List[Account]           │
│ - state_fields: List[Field]         │
├─────────────────────────────────────┤
│ + initialize()                      │
│ + get_accounts()                    │
│ + get_account(account_id: str)      │
│ + store_state()                     │
│ + load_state()                      │
│ + validate_credentials()            │
└─────────────────────────────────────┘
```

### Account Class

The Account class manages credentials for specific service instances:

```
┌─────────────────────────────────────┐
│              Account                │
├─────────────────────────────────────┤
│ - account_id: str                   │
│ - account_name: str                 │
│ - service_id: str                   │
│ - credentials: Dict[str, Any]       │
│ - is_active: bool                   │
├─────────────────────────────────────┤
│ + validate()                        │
│ + get_credential(key: str)          │
│ + set_credential(key: str, value)   │
│ + test_connection()                 │
└─────────────────────────────────────┘
```

### Service Discovery

The system dynamically discovers services through:
1. Class inheritance detection
2. Docker container inspection
3. Service registration in Redis

### State Management

Services can tag fields for persistence in Redis:
- Fields marked with JSON extras are automatically synchronized
- State is loaded on service initialization
- Changes are persisted in real-time
- Redis ensures data consistency across restarts

## Authentication Flow

1. The system identifies services that require accounts
2. Users create and configure accounts for services through the UI
3. Account credentials are securely stored in Redis
4. Services access accounts and their credentials when making API calls
5. Accounts can be validated independently of service initialization
6. Multiple accounts can be created for a single service
7. Services can specify which account to use for specific operations

## Task Management

Task scheduling and management is handled by:
- Celery for distributed task execution
- Flower for monitoring and administration
- Redis as the message broker
- Persistent job storage for reliability

## UI Scaling

The UI is designed to scale with the growing number of MCP servers:
- Dynamic service discovery updates the UI automatically
- Hierarchical menu structure accommodates numerous services
- Categorization of services for better organization
- Pagination or scrolling for large numbers of services

## Communication Flow

1. User interacts with the system tray application
2. Requests are routed to the appropriate service
3. Services process requests and update their state
4. State changes are persisted to Redis
5. UI components reflect the updated state

## Deployment Architecture

The MCP Suite is deployed as:
- A standalone application for the system tray component
- Docker containers for individual MCP servers
- A local Redis instance for state management
- Celery workers for background task processing
- Flower dashboard for task monitoring

## Extensibility

The architecture supports extensibility through:
- Plug-and-play service integration
- Standardized service interfaces
- Dynamic discovery of new services
- Configuration-driven behavior
- State persistence for service continuity 

## MCP Tool Decorators

The MCP Suite implements a decorator pattern for enhancing MCP tools with additional capabilities:

```
┌─────────────────────────────────────┐
│           BaseMCPDecorator          │
├─────────────────────────────────────┤
│ - wrapped_tool: Callable            │
├─────────────────────────────────────┤
│ + call(args, kwargs)                │
│ + pre_execution_hook()              │
│ + post_execution_hook()             │
│ + error_handling_hook()             │
└─────────────────────────────────────┘
```

### Core Decorators

These decorators mutate the function's signature and docstring, giving the tool extra arguments and capabilities.

#### 1. Scheduler Decorator

The `@scheduler` decorator enables MCP tools to be scheduled for execution:

```
┌─────────────────────────────────────┐
│           SchedulerDecorator        │
├─────────────────────────────────────┤
│ - celery_app: Celery                │
│ - schedule_options: Dict            │
├─────────────────────────────────────┤
│ + schedule(cron_expr, args, kw)     │
│ + cancel_scheduled(task_id)         │
│ + list_scheduled_tasks()            │
│ + modify_schedule(task_id, new_expr)│
└─────────────────────────────────────┘
```

#### 2. DataFrame Decorator

The `@dataframe` decorator provides MCP tools with capabilities to read from and write to dataframes:

```
┌─────────────────────────────────────┐
│           DataFrameDecorator        │
├─────────────────────────────────────┤
│ - supported_formats: List[str]      │
│ - default_format: str               │
├─────────────────────────────────────┤
│ + read_df(source, format=None)      │
│ + write_df(df, target, format=None) │
│ + transform_df(df, transform_func)  │
│ + get_schema(df)                    │
└─────────────────────────────────────┘
```

#### 3. Logger Decorator

The `@logger` decorator automatically logs MCP tool execution details using loguru:

```
┌─────────────────────────────────────┐
│           LoggerDecorator           │
├─────────────────────────────────────┤
│ - log_level: str                    │
│ - log_format: str                   │
│ - log_file: str                     │
├─────────────────────────────────────┤
│ + configure_logger(config: Dict)    │
│ + log_execution(status, details)    │
│ + get_execution_history()           │
└─────────────────────────────────────┘
```

### Decorator Composition

MCP tool decorators can be composed to provide multiple capabilities:

```python
@mcp.tool()
@scheduler
@dataframe
@logger(level="DEBUG")
def etl_process(source_path, target_path):
    # Implementation combining scheduling, dataframe operations, and logging
    pass
```

## Integration with Other Components

The architecture described in this document is implemented using the technologies specified in the [Technology Stack](technology_stack.md) document and follows the development plan outlined in the [Sprint Development Plan](sprint_development_plan.md).

