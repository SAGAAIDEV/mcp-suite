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

# Code Knowledge Graph Schema

This document outlines the schema for a Neo4j knowledge graph designed to represent the structure and relationships in a codebase.

## Overview

The knowledge graph captures code structure at multiple levels (files, functions, classes, etc.) and their relationships (imports, calls, tests, etc.). This enables powerful queries for understanding code dependencies, test coverage, and other aspects of the codebase.

## Node Types

### File
Represents source code and test files in the codebase.

**Properties:**
- `path`: The file's full path
- `name`: The filename
- `type`: File type (e.g., Python, JavaScript)
- `isTest`: Boolean flag for test files

### Function
Represents a function in the codebase.

**Properties:**
- `name`: Function name
- `signature`: Full function signature
- `returnType`: Return type
- `lineStart`: Starting line number
- `lineEnd`: Ending line number
- `docstring`: Function documentation

### Class
Represents a class in the codebase.

**Properties:**
- `name`: Class name
- `lineStart`: Starting line number
- `lineEnd`: Ending line number
- `docstring`: Class documentation

### Method
Represents a method within a class.

**Properties:**
- `name`: Method name
- `signature`: Full method signature
- `returnType`: Return type
- `lineStart`: Starting line number
- `lineEnd`: Ending line number
- `docstring`: Method documentation
- `isStatic`: Boolean flag for static methods

### Variable
Represents a variable in the codebase.

**Properties:**
- `name`: Variable name
- `type`: Variable type
- `lineNumber`: Line number where defined
- `scope`: Scope (global, local, class)

### TestCase
Represents a test function or method.

**Properties:**
- `name`: Test name
- `lineStart`: Starting line number
- `lineEnd`: Ending line number
- `testType`: Type of test (unit, integration, etc.)

## Relationship Types

### CONTAINS
Connects containers to their contents.

**Direction:** File → Function/Class/Variable, Class → Method/Variable

**Properties:**
- `visibility`: Public, private, protected

### IMPORTS
Connects files that import other files.

**Direction:** File → File

**Properties:**
- `importType`: Direct, relative, aliased
- `alias`: Name if imported with alias

### CALLS
Connects functions/methods that call other functions/methods.

**Direction:** Function → Function, Method → Method, Function → Method, Method → Function

**Properties:**
- `callCount`: Number of times called
- `lineNumbers`: Line numbers of calls
- `parameters`: Parameters passed

### INHERITS_FROM
Connects classes that inherit from other classes.

**Direction:** Class → Class

**Properties:**
- `inheritanceType`: Single, multiple

### TESTS
Connects tests to the code they test.

**Direction:** TestCase → Function/Method/Class

**Properties:**
- `testCoverage`: Percentage of code covered
- `testResult`: Pass/Fail status from latest run

### HAS_TEST
The inverse of TESTS, connects code to its tests.

**Direction:** File → File (Production file to Test file), Function/Method/Class → TestCase

**Properties:**
- `coverage`: Coverage percentage
- `lastVerified`: Timestamp of last verification

### DEPENDS_ON
Connects code to variables it depends on.

**Direction:** Function/Method → Variable

**Properties:**
- `dependencyType`: Read, write, both

### INSTANTIATES
Connects code that creates instances of classes.

**Direction:** Function/Method → Class

**Properties:**
- `instanceCount`: Number of instantiations

### REFERENCES
General-purpose relationship for any reference between nodes.

**Direction:** Any node → Any node

**Properties:**
- `referenceType`: Direct, indirect
- `lineNumbers`: Lines where reference occurs

### IMPLEMENTS
Connects classes to interfaces they implement.

**Direction:** Class → Interface (for languages with interfaces)

## Example Queries

### Find all test cases for a specific function
```cypher
MATCH (f:Function {name: 'validate_file_path'})-[:HAS_TEST]->(t:TestCase)
RETURN f.name as function, collect(t.name) as testCases
```

### Find all functions a function calls (dependencies)
```cypher
MATCH (f:Function {name: 'validate_file_path'})-[:CALLS]->(dependency:Function)
RETURN f.name as function, collect(dependency.name) as dependencies
```

### Find files without tests
```cypher
MATCH (f:File)
WHERE f.isTest = false AND NOT (f)-[:HAS_TEST]->()
RETURN f.name as filesWithoutTests
```

### Find test coverage information
```cypher
MATCH (source)-[testRel:TESTS]->(target)
RETURN 
    CASE 
        WHEN source:File THEN 'File' 
        WHEN source:TestCase THEN 'TestCase' 
    END as sourceType,
    source.name as source,
    CASE 
        WHEN target:File THEN 'File' 
        WHEN target:Function THEN 'Function'
    END as targetType,
    target.name as target,
    testRel.testCoverage as coveragePercentage
```

### Find all import relationships
```cypher
MATCH (source:File)-[importRel:IMPORTS]->(target:File)
RETURN source.name as sourceFile, target.name as importedFile, importRel.importType as importType
```

## Implementation

To implement this knowledge graph:

1. Parse the codebase to extract entities and relationships
2. Store them in Neo4j using the schema above
3. Write queries to extract useful information
4. Visualize the relationships to understand the codebase structure

## Benefits

- Complete code traceability
- Test coverage insights
- Impact analysis for code changes
- Documentation enhancement
- Code quality metrics
- Identification of:
  - Dead code
  - Tightly coupled components
  - Test gaps
  - Module dependencies
  - Data flow

## Example Code

The following Cypher query creates a simple knowledge graph for a validation module and its tests:

```cypher
// Create Files
CREATE (validation:File {path: 'src/mcp_suite/servers/qa/tools/testing/lib/validation.py', name: 'validation.py', type: 'Python', isTest: false})
CREATE (testValidation:File {path: 'src/tests/unit/test_servers/test_qa/test_tools/test_testing/test_lib/test_validation.py', name: 'test_validation.py', type: 'Python', isTest: true})
CREATE (files:File {path: 'src/mcp_suite/servers/qa/utils/files.py', name: 'files.py', type: 'Python', isTest: false})

// Create Functions in validation.py
CREATE (validateFilePath:Function {name: 'validate_file_path', signature: 'validate_file_path(file_path: str, tool_function) -> ToolResult', returnType: 'ToolResult', lineStart: 22, lineEnd: 55, docstring: 'Validate that the provided file path is a valid Python file.'})
CREATE (validateCoverageModule:Function {name: 'validate_coverage_module', signature: 'validate_coverage_module(coverage_module: str, tool_function) -> ToolResult', returnType: 'ToolResult', lineStart: 58, lineEnd: 101, docstring: 'Validate that the provided coverage module exists and can be imported.'})

// Create Functions in files.py
CREATE (isValidPythonPath:Function {name: 'is_valid_python_path', signature: 'is_valid_python_path(path: str) -> bool', returnType: 'bool', lineStart: 4, lineEnd: 38, docstring: 'Check if a path is a valid Python file.'})

// Create Test cases
CREATE (testValidFilePath:TestCase {name: 'test_valid_file_path', lineStart: 15, lineEnd: 28, testType: 'unit'})
CREATE (testInvalidPythonPathFormat:TestCase {name: 'test_invalid_python_path_format', lineStart: 30, lineEnd: 45, testType: 'unit'})
CREATE (testNonexistentFilePath:TestCase {name: 'test_nonexistent_file_path', lineStart: 47, lineEnd: 71, testType: 'unit'})
CREATE (testDotDirectoryPath:TestCase {name: 'test_dot_directory_path', lineStart: 73, lineEnd: 85, testType: 'unit'})

// Connect Files to Functions
CREATE (validation)-[:CONTAINS {visibility: 'public'}]->(validateFilePath)
CREATE (validation)-[:CONTAINS {visibility: 'public'}]->(validateCoverageModule)
CREATE (files)-[:CONTAINS {visibility: 'public'}]->(isValidPythonPath)

// Connect Test File to Test Cases
CREATE (testValidation)-[:CONTAINS {visibility: 'public'}]->(testValidFilePath)
CREATE (testValidation)-[:CONTAINS {visibility: 'public'}]->(testInvalidPythonPathFormat)
CREATE (testValidation)-[:CONTAINS {visibility: 'public'}]->(testNonexistentFilePath)
CREATE (testValidation)-[:CONTAINS {visibility: 'public'}]->(testDotDirectoryPath)

// File Imports
CREATE (validation)-[:IMPORTS {importType: 'direct'}]->(files)

// Function Calls
CREATE (validateFilePath)-[:CALLS {callCount: 1, lineNumbers: [35]}]->(isValidPythonPath)

// Test Relationships
CREATE (testValidation)-[:TESTS {testCoverage: 100}]->(validation)
CREATE (testValidFilePath)-[:TESTS {testCoverage: 25}]->(validateFilePath)
CREATE (testInvalidPythonPathFormat)-[:TESTS {testCoverage: 25}]->(validateFilePath)
CREATE (testNonexistentFilePath)-[:TESTS {testCoverage: 25}]->(validateFilePath)
CREATE (testDotDirectoryPath)-[:TESTS {testCoverage: 25}]->(validateFilePath)

// HAS_TEST Relationships
CREATE (validation)-[:HAS_TEST {coverage: 100, lastVerified: datetime()}]->(testValidation)
CREATE (validateFilePath)-[:HAS_TEST {coverage: 100, lastVerified: datetime()}]->(testValidFilePath)
CREATE (validateFilePath)-[:HAS_TEST {coverage: 100, lastVerified: datetime()}]->(testInvalidPythonPathFormat)
CREATE (validateFilePath)-[:HAS_TEST {coverage: 100, lastVerified: datetime()}]->(testNonexistentFilePath)
CREATE (validateFilePath)-[:HAS_TEST {coverage: 100, lastVerified: datetime()}]->(testDotDirectoryPath)
``` 
