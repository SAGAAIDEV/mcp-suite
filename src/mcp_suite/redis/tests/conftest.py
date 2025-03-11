# conftest.py
import os
import sys
import types
from unittest.mock import MagicMock

# Set required environment variables early
os.environ["REDDIT_CLIENT_ID"] = "dummy_client_id"
os.environ["REDDIT_CLIENT_SECRET"] = "dummy_client_secret"
os.environ["LLM_OPENAI_API_KEY"] = "dummy_openai_key"
os.environ["LLM_ANTHROPIC_API_KEY"] = "dummy_anthropic_key"
os.environ["LLM_GEMINI_API_KEY"] = "dummy_gemini_key"
os.environ["ZOOM_CLIENT_ID"] = "dummy_zoom_client_id"
os.environ["ZOOM_CLIENT_CREDENTIALS"] = "dummy_zoom_client_credentials"
os.environ["ASSEMBLYAI_API_KEY"] = "dummy_assemblyai_api_key"
os.environ["BLUESKY_USERNAME"] = "dummy_bluesky_username"
os.environ["BLUESKY_PASSWORD"] = "dummy_bluesky_password"
os.environ["BLUESKY_EMAIL"] = "dummy_bluesky_email"
os.environ["CONFLUENCE_API_TOKEN"] = "dummy_confluence_api_token"
os.environ["CONFLUENCE_EMAIL"] = "dummy_confluence_email"
os.environ["CONFLUENCE_URL"] = "dummy_confluence_url"

# Create dummy configuration classes
class MockLLM:
    OPENAI_API_KEY = "dummy_openai_key"
    ANTHROPIC_API_KEY = "dummy_anthropic_key"
    GEMINI_API_KEY = "dummy_gemini_key"

class MockReddit:
    CLIENT_ID = "dummy_client_id"
    CLIENT_SECRET = "dummy_client_secret"
    USERNAME = "dummy_username"
    PASSWORD = "dummy_password"
    USER_AGENT = "mcp-reddit-server"

class MockZoom:
    CLIENT_ID = "dummy_zoom_client_id"
    CLIENT_CREDENTIALS = "dummy_zoom_client_credentials"

class MockAssemblyAI:
    API_KEY = "dummy_assemblyai_api_key"

class MockBluesky:
    USERNAME = "dummy_bluesky_username"
    PASSWORD = "dummy_bluesky_password"
    EMAIL = "dummy_bluesky_email"

class MockConfluence:
    API_TOKEN = "dummy_confluence_api_token"
    EMAIL = "dummy_confluence_email"
    URL = "dummy_confluence_url"

class MockRedisConfig:
    URL = "redis://localhost:6379"
    DB_PATH = "/tmp/redis-db"
    DB = "mcp"

# Build a dummy 'env' module for src.config.env using types.ModuleType
dummy_env = types.ModuleType("env")
dummy_env.REDIS = MockRedisConfig()
dummy_env.REDDIT = MockReddit()
dummy_env.LLM = MockLLM()
dummy_env.LLM_API_KEYS = MockLLM()
dummy_env.ZOOM = MockZoom()
dummy_env.BLUESKY = MockBluesky()
dummy_env.CONFLUENCE = MockConfluence()
dummy_env.AssemblyAI = MockAssemblyAI()

# Override the real config module so that when it's imported it uses our dummy config.
sys.modules["src.config.env"] = dummy_env

# Create mock Redis module with ConnectionError
class ConnectionError(Exception):
    """Mock Redis ConnectionError"""
    pass

dummy_redis = types.ModuleType("redis")
dummy_redis.ConnectionError = ConnectionError
# If you want to override certain parts, assign them here (or let the real redis be used)
# For example, you might later patch redis.Redis in specific tests.
sys.modules["redis"] = dummy_redis

# Create a proper mock of the loguru logger
mock_logger = MagicMock()
mock_logger.add = MagicMock(return_value=1)
mock_logger.remove = MagicMock()
mock_logger.info = MagicMock()
mock_logger.debug = MagicMock()
mock_logger.warning = MagicMock()
mock_logger.error = MagicMock()
mock_logger.critical = MagicMock()
mock_logger.exception = MagicMock()

dummy_loguru = types.ModuleType("loguru")
dummy_loguru.logger = mock_logger
sys.modules["loguru"] = dummy_loguru
