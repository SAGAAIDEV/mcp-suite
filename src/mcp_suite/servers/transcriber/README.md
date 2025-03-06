# Transcriber MCP Service

This package provides audio transcription services using AssemblyAI through the MCP framework.

## Features

- Transcribe audio files to text
- Support for multiple languages
- Support for various audio formats
- Validation of audio files and language codes

## Structure

The package follows a modular structure:

- `apis/`: Contains the API modules for interacting with AssemblyAI
- `servers/`: Contains the MCP server implementations
- `utils/`: Contains utility functions for file operations
- `config/`: Contains configuration settings

## Usage

### Environment Setup

1. Make sure you have an AssemblyAI API key
2. Set the API key in your environment:
   ```
   export ASSEMBLYAI_API_KEY=your_api_key
   ```
   or create a `.env` file with:
   ```
   ASSEMBLYAI_API_KEY=your_api_key
   ```

### Running the Service

Run the service as a module:

```bash
python -m src.services.mcp.transcriber
```

Or run the server directly:

```bash
python src/services/mcp/transcriber/servers/transcriber_server.py
```

## Supported Languages

The service supports the following languages:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Dutch (nl)
- Japanese (ja)
- Korean (ko)
- Chinese (zh)
- Russian (ru)

## Supported Audio Formats

The service supports the following audio formats:
- MP3 (.mp3)
- MP4 (.mp4)
- WAV (.wav)
- OGG (.ogg)
- FLAC (.flac)
- M4A (.m4a)
- WebM (.webm)

## Dependencies

- assemblyai: For audio transcription
- mcp: For FastMCP server implementation
- python-dotenv: For environment variable loading 