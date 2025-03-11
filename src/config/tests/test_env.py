"""
Tests for the env.py module.
"""

import os
from pathlib import Path

# Set required environment variables before importing the modules
os.environ["REDDIT_CLIENT_ID"] = "test_client_id"
os.environ["REDDIT_CLIENT_SECRET"] = "test_client_secret"
os.environ["ZOOM_CLIENT_ID"] = "test_zoom_client_id"
os.environ["ZOOM_CLIENT_CREDENTIALS"] = "test_zoom_credentials"
os.environ["ASSEMBLYAI_API_KEY"] = "test_assemblyai_key"
os.environ["BLUESKY_USERNAME"] = "test_bluesky_username"
os.environ["BLUESKY_PASSWORD"] = "test_bluesky_password"
os.environ["BLUESKY_EMAIL"] = "test_bluesky_email"
os.environ["CONFLUENCE_API_TOKEN"] = "test_confluence_token"
os.environ["CONFLUENCE_EMAIL"] = "test_confluence_email"
os.environ["CONFLUENCE_URL"] = "test_confluence_url"

# Now import the modules
from src.config.env import (
    ASSEMBLYAI,
    BLUESKY,
    CELERY,
    CONFLUENCE,
    FLOWER,
    LLM_API_KEYS,
    PATHS,
    REDDIT,
    REDIS,
    SESSION,
    TWITCH,
    ZOOM,
)


def test_twitch_stream_url():
    """Test the STREAM_URL property of the Twitch class."""
    # Test with STREAM_KEY set
    original_stream_key = TWITCH.STREAM_KEY
    try:
        # Set a test stream key
        TWITCH.STREAM_KEY = "test_stream_key"
        assert TWITCH.STREAM_URL == "rtmp://live.twitch.tv/app/test_stream_key"

        # Test with STREAM_KEY not set
        TWITCH.STREAM_KEY = None
        assert TWITCH.STREAM_URL is None
    finally:
        # Restore original value
        TWITCH.STREAM_KEY = original_stream_key


def test_celery_broker_url():
    """Test the get_broker_url method of the Celery class."""
    # Test with BROKER_URL set
    original_broker_url = CELERY.BROKER_URL
    try:
        # Set a test broker URL
        CELERY.BROKER_URL = "test_broker_url"
        assert CELERY.get_broker_url() == "test_broker_url"

        # Test with BROKER_URL not set (should default to REDIS.URL)
        CELERY.BROKER_URL = None
        assert CELERY.get_broker_url() == REDIS.URL
    finally:
        # Restore original value
        CELERY.BROKER_URL = original_broker_url


def test_celery_backend_url():
    """Test the get_backend_url method of the Celery class."""
    # Test with BACKEND_URL set
    original_backend_url = CELERY.BACKEND_URL
    try:
        # Set a test backend URL
        CELERY.BACKEND_URL = "test_backend_url"
        assert CELERY.get_backend_url() == "test_backend_url"

        # Test with BACKEND_URL not set (should default to REDIS.URL)
        CELERY.BACKEND_URL = None
        assert CELERY.get_backend_url() == REDIS.URL
    finally:
        # Restore original value
        CELERY.BACKEND_URL = original_backend_url


def test_llm_settings():
    """Test the LLM settings class."""
    assert hasattr(LLM_API_KEYS, "OPENAI_API_KEY")
    assert hasattr(LLM_API_KEYS, "ANTHROPIC_API_KEY")
    assert hasattr(LLM_API_KEYS, "GEMINI_API_KEY")

    # Test model_config attributes
    assert LLM_API_KEYS.model_config.get("env_file") == ".env"
    assert LLM_API_KEYS.model_config.get("case_sensitive") is True
    assert LLM_API_KEYS.model_config.get("env_prefix") == "LLM_"


def test_paths_settings():
    """Test the Paths settings class."""
    assert isinstance(PATHS.BASE_DIR, Path)
    assert PATHS.AUDIO_FILENAME == "audio.mp4"
    assert PATHS.EDIT_FILENAME == "edit.mp4"
    assert PATHS.CAMERA_FILENAME == "camera.mp4"
    assert PATHS.SCREENRECORD_FILENAME == "screen.mp4"
    assert PATHS.STREAM_FILENAME == "stream.mp4"


def test_reddit_settings():
    """Test the Reddit settings class."""
    # Check that our mocked values were used
    assert REDDIT.CLIENT_ID == "test_client_id"
    assert REDDIT.CLIENT_SECRET == "test_client_secret"
    assert hasattr(REDDIT, "USERNAME")
    assert hasattr(REDDIT, "PASSWORD")
    assert REDDIT.USER_AGENT == "mcp-reddit-server"


def test_zoom_settings():
    """Test the Zoom settings class."""
    assert ZOOM.CLIENT_ID == "test_zoom_client_id"
    assert ZOOM.CLIENT_CREDENTIALS == "test_zoom_credentials"
    assert ZOOM.model_config.get("env_prefix") == "ZOOM_"


def test_assemblyai_settings():
    """Test the AssemblyAI settings class."""
    assert ASSEMBLYAI.API_KEY == "test_assemblyai_key"
    assert ASSEMBLYAI.model_config.get("env_prefix") == "ASSEMBLYAI_"


def test_session_state_settings():
    """Test the SessionState settings class."""
    assert isinstance(SESSION.CHAT_SESSION_PATH, Path)
    assert SESSION.CHAT_SESSION_PATH == Path("chat_session.json")
    assert SESSION.model_config.get("env_prefix") == "SESSION_"


def test_bluesky_settings():
    """Test the Bluesky settings class."""
    assert BLUESKY.USERNAME == "test_bluesky_username"
    assert BLUESKY.PASSWORD == "test_bluesky_password"
    assert BLUESKY.EMAIL == "test_bluesky_email"
    assert BLUESKY.model_config.get("env_prefix") == "BLUESKY_"


def test_confluence_settings():
    """Test the Confluence settings class."""
    assert CONFLUENCE.API_TOKEN == "test_confluence_token"
    assert CONFLUENCE.EMAIL == "test_confluence_email"
    assert CONFLUENCE.URL == "test_confluence_url"
    assert CONFLUENCE.model_config.get("env_prefix") == "CONFLUENCE_"


def test_redis_settings():
    """Test the Redis settings class."""
    assert REDIS.URL == "redis://localhost:6379/0"
    assert REDIS.DB == "mcp"
    assert REDIS.model_config.get("env_prefix") == "REDIS_"


def test_celery_settings():
    """Test the Celery settings class attributes."""
    assert CELERY.APP_NAME == "mcp_scheduler"
    assert CELERY.RESULT_EXPIRES == 3600
    assert CELERY.TASK_SERIALIZER == "json"
    assert CELERY.RESULT_SERIALIZER == "json"
    assert CELERY.ACCEPT_CONTENT == ["json"]
    assert CELERY.TIMEZONE == "UTC"
    assert CELERY.ENABLE_UTC is True


def test_flower_settings():
    """Test the Flower settings class."""
    assert FLOWER.BROKER_API == REDIS.URL
    assert FLOWER.ADDRESS == "0.0.0.0"
    assert FLOWER.PORT == 5555
    assert FLOWER.URL_PREFIX == ""
    assert FLOWER.BASIC_AUTH == ""
    assert FLOWER.MAX_TASKS == 10000
    assert FLOWER.DB == "flower.db"
    assert FLOWER.model_config.get("env_prefix") == "FLOWER_"
