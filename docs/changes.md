# MCP Suite - Change Log

This document tracks all significant changes to the MCP Suite project, including files added, modified, and removed.

## [Unreleased]

### Added
- Created `.github/workflows/lint-test.yml` for automated linting and testing on push/PR
- Moved `.flake8` configuration to `.github/.flake8` for centralized CI configuration
- Added `README.md` to `/src/mcp_suite` with module documentation
- Added `changes.md` to `/docs` for tracking project changes

### Changed
- Updated project structure to better support CI/CD workflows

### Removed
- Removed root-level `.flake8` file (moved to `.github/.flake8`)

## [0.1.0] - 2023-03-01

### Added
- Initial project structure
- Basic system tray application framework
- Redis integration for state management
- Docker integration for container management
- Configuration management
- Documentation framework
- Testing framework

### Changed
- N/A (initial release)

### Removed
- N/A (initial release)

## Change Types

When adding entries to this change log, use the following categories:

- **Added**: New features or files
- **Changed**: Updates to existing functionality
- **Deprecated**: Features that will be removed in upcoming releases
- **Removed**: Features or files that have been removed
- **Fixed**: Bug fixes
- **Security**: Vulnerabilities that have been addressed