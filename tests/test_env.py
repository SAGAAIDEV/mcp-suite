"""
Tests for the env.py module.
"""

from src.config.env import CELERY, REDIS, TWITCH


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
