# Midjourney MCP Technical Requirements

## Overview

This document outlines the technical requirements for implementing a Machine Control Protocol (MCP) server that interfaces with Midjourney's image generation API. The server will allow AI agents to create, modify, and retrieve AI-generated images through a standardized interface.

## Authentication Requirements

### API Key Management

1. **Key Storage Options**
   - Environment variable: `MIDJOURNEY_API_KEY`
   - Configuration file (YAML format)
   - Web UI input with secure storage
   - Command-line configuration utility

2. **Discord Authentication Automation (Optional)**
   - Playwright-based script to:
     - Log in to Discord using provided credentials
     - Navigate to Midjourney interface
     - Extract API key using browser inspector
     - Store key securely in configuration
   - Manual fallback option for key entry

3. **Security Requirements**
   - Encrypted storage of API keys
   - Secure handling of Discord credentials
   - Key validation before storage
   - Proper access controls for key retrieval

## Webhook Integration

### Webhook Server Requirements

1. **Public Endpoint**
   - Publicly accessible FastAPI server to receive Midjourney callbacks
   - Configurable domain/URL for webhook registration
   - SSL/TLS support for secure communication
   - IP filtering for additional security (optional)

2. **Webhook Registration**
   - Automatic registration of webhook URL with Midjourney API
   - Webhook verification process handling
   - Webhook secret management for payload validation
   - Periodic webhook validation to ensure connectivity

3. **Webhook Handler**
   - Endpoint to receive image generation completion notifications
   - Payload validation and security checks
   - Event processing and correlation with pending requests
   - Error handling for malformed or unexpected payloads

4. **Deployment Options**
   - Cloud deployment (AWS, GCP, Azure)
   - Self-hosted with proper port forwarding
   - Serverless function option (AWS Lambda, etc.)
   - ngrok or similar for development/testing

### Asynchronous Processing

1. **Request-Response Flow**
   - Initial request returns a job ID immediately
   - Webhook notification updates job status
   - Polling endpoint for job status checks
   - Event-driven architecture for notification handling

2. **Job Management**
   - Persistent job queue with status tracking
   - Correlation between outgoing requests and webhook callbacks
   - Timeout handling for stalled jobs
   - Retry mechanisms for failed requests

## MCP Server Implementation

### Core Server Requirements

1. **FastAPI Framework**
   - Asynchronous request handling
   - OpenAPI documentation generation
   - Proper error handling and status codes
   - Request validation and type checking

2. **Standard MCP Endpoints**
   - `/imagine` - Process text prompts into images
   - `/upscale` - Enhance resolution of generated images
   - `/variation` - Create variations of existing images
   - `/version` - Select Midjourney version
   - `/images` - List and retrieve generated images
   - `/config` - Manage server configuration
   - `/jobs/{job_id}` - Check status of pending jobs
   - `/webhook/midjourney` - Receive Midjourney callbacks

3. **Response Format**
   - Consistent JSON structure
   - Standard error format
   - Image URLs or Base64 encoded images
   - Complete metadata for generated images
   - Job status information for async operations

### Configuration System

1. **Configuration Structure**
   ```yaml
   # Example configuration
   api:
     midjourney_key: "encrypted_key_here"
     key_source: "manual|environment|discord"
     
   server:
     host: "0.0.0.0"
     port: 8000
     workers: 4
     
   storage:
     type: "local"
     path: "./images"
     retention_days: 30
     
   discord_automation:
     enabled: false
     credentials_stored: false
     
   webhook:
     public_url: "https://your-domain.com/webhook/midjourney"
     secret: "webhook_secret_key"
     verification_token: "verification_token"
     ssl_enabled: true
   ```

2. **Configuration Management**
   - File-based configuration with proper permissions
   - Environment variable overrides
   - API endpoints for configuration updates
   - Configuration validation on load/update

## User Interface Requirements

1. **Web-based Configuration UI**
   - Simple dashboard for server status
   - Secure form for API key management
   - Option to trigger Discord automation
   - Configuration testing functionality
   - Mobile-responsive design
   - Webhook configuration and testing

2. **API Key Setup Flow**
   - Option 1: Direct API key entry
   - Option 2: Environment variable configuration
   - Option 3: Discord automation with credentials
   - Validation and testing of entered keys

3. **Webhook Management**
   - Webhook URL configuration
   - Test webhook functionality
   - View webhook event history
   - Troubleshooting tools for webhook issues

## Implementation Details

### Discord Automation Process

1. **Initialization**
   - Launch headless browser via Playwright
   - Navigate to Discord login page
   - Handle login form with provided credentials
   - Navigate to Midjourney interface

2. **Key Extraction**
   - Identify network requests to Midjourney API
   - Extract authentication token/key
   - Validate key format and test functionality
   - Securely store extracted key

3. **Security Considerations**
   - Option to run automation once without storing credentials
   - Secure handling of browser session
   - Proper cleanup after key extraction
   - Clear error handling for authentication issues

### Webhook Implementation

1. **Webhook Server**
   - FastAPI server with dedicated webhook endpoints
   - Request signature validation
   - Event type routing and handling
   - Logging of all webhook events

2. **Event Processing**
   - Parse incoming webhook payloads
   - Match events to pending job requests
   - Update job status in database
   - Trigger notifications or callbacks as needed

3. **Polling Mechanism**
   - Client-side polling for job status updates
   - Exponential backoff for efficient polling
   - WebSocket option for real-time updates (optional enhancement)
   - Timeout handling for abandoned jobs

### API Implementation

1. **Midjourney Client**
   - Handle authentication with Midjourney API
   - Format requests according to Midjourney specifications
   - Process and validate responses
   - Handle rate limiting and errors
   - Register and manage webhook configuration

2. **Image Storage**
   - Local file storage with organized directory structure
   - Metadata database for quick retrieval
   - Cleanup policy for old images
   - Backup and recovery mechanisms

3. **Job Queue**
   - Persistent storage of job information
   - Status tracking (pending, processing, completed, failed)
   - Correlation with webhook events
   - Job expiration and cleanup

## Testing Requirements

1. **Unit Tests**
   - Configuration management
   - API endpoint functionality
   - Authentication handling
   - Error handling
   - Webhook payload processing

2. **Integration Tests**
   - End-to-end image generation flow
   - Configuration update process
   - Discord automation (with mock Discord)
   - Webhook event handling
   - Performance under load

3. **Webhook Testing**
   - Mock webhook events for testing
   - Webhook registration verification
   - Error handling for webhook failures
   - Timeout and retry behavior

## Deployment Considerations

1. **Docker Support**
   - Containerized deployment option
   - Environment-based configuration
   - Volume mapping for persistent storage
   - Health check endpoints

2. **Production Readiness**
   - Logging configuration
   - Monitoring endpoints
   - Resource usage optimization
   - Backup and recovery procedures

3. **Webhook Server Deployment**
   - Public-facing server with proper security
   - SSL/TLS certificate management
   - Domain name configuration
   - Firewall and access control

## Documentation Requirements

1. **API Documentation**
   - OpenAPI/Swagger documentation
   - Example requests and responses
   - Error code reference
   - Rate limiting information
   - Webhook payload formats

2. **Setup Guide**
   - Installation instructions
   - Configuration options
   - Discord automation setup
   - Webhook server deployment
   - Troubleshooting common issues

3. **Architecture Diagram**
   - Component interaction overview
   - Request flow visualization
   - Webhook integration diagram
   - Deployment architecture options 