# Global conftest.py
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
dummy_redis.Redis = MagicMock()
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

# Create a proper loguru module with a logger attribute
dummy_loguru = types.ModuleType("loguru")
dummy_loguru.logger = mock_logger
sys.modules["loguru"] = dummy_loguru

# Create a mock for assemblyai
dummy_assemblyai = types.ModuleType("assemblyai")
dummy_assemblyai.Transcript = MagicMock()
sys.modules["assemblyai"] = dummy_assemblyai

# Create a mock for atproto
dummy_atproto = types.ModuleType("atproto")
dummy_atproto.Client = MagicMock()
sys.modules["atproto"] = dummy_atproto

# Create a mock for pydantic
dummy_pydantic = types.ModuleType("pydantic")
dummy_pydantic.networks = types.ModuleType("pydantic.networks")
dummy_pydantic.networks.AnyUrl = MagicMock()
dummy_pydantic.networks.UrlConstraints = MagicMock()
sys.modules["pydantic"] = dummy_pydantic
sys.modules["pydantic.networks"] = dummy_pydantic.networks

# Create a mock for mcp
dummy_mcp = types.ModuleType("mcp")
dummy_mcp.server = types.ModuleType("mcp.server")
dummy_mcp.server.fastmcp = types.ModuleType("mcp.server.fastmcp")
dummy_mcp.server.fastmcp.FastMCP = MagicMock()
dummy_mcp.client = types.ModuleType("mcp.client")
dummy_mcp.client.session = types.ModuleType("mcp.client.session")
dummy_mcp.client.session.ClientSession = MagicMock()
dummy_mcp.types = types.ModuleType("mcp.types")
sys.modules["mcp"] = dummy_mcp
sys.modules["mcp.server"] = dummy_mcp.server
sys.modules["mcp.server.fastmcp"] = dummy_mcp.server.fastmcp
sys.modules["mcp.client"] = dummy_mcp.client
sys.modules["mcp.client.session"] = dummy_mcp.client.session
sys.modules["mcp.types"] = dummy_mcp.types