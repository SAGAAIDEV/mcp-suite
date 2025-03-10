from pathlib import Path
from typing import List, Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class LLM(BaseSettings):
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="LLM_",
    )


LLM_API_KEYS = LLM()


class Paths(BaseSettings):
    # Base paths
    BASE_DIR: Path = Path(__file__).parent.parent

    # Database settings
    AUDIO_FILENAME: Optional[str] = "audio.mp4"
    EDIT_FILENAME: Optional[str] = "edit.mp4"
    CAMERA_FILENAME: Optional[str] = "camera.mp4"
    SCREENRECORD_FILENAME: Optional[str] = "screen.mp4"
    STREAM_FILENAME: Optional[str] = "stream.mp4"

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="allow"
    )


PATHS = Paths()


class Twitch(BaseSettings):
    STREAM_KEY: Optional[str] = None
    STREAMINFO_CLIENTID: Optional[str] = None
    STREAMINFO_SECRET: Optional[str] = None

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="TWITCH_",
    )

    @property
    def STREAM_URL(self) -> Optional[str]:
        if self.STREAM_KEY:
            return f"rtmp://live.twitch.tv/app/{self.STREAM_KEY}"
        return None


TWITCH = Twitch()


class Reddit(BaseSettings):
    CLIENT_ID: str
    CLIENT_SECRET: str
    USERNAME: Optional[str] = None
    PASSWORD: Optional[str] = None
    USER_AGENT: str = "mcp-reddit-server"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="REDDIT_",
    )


REDDIT = Reddit()


class Zoom(BaseSettings):
    CLIENT_ID: str
    CLIENT_CREDENTIALS: str

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="ZOOM_",
    )


ZOOM = Zoom()


class AssemblyAI(BaseSettings):
    API_KEY: str

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="ASSEMBLYAI_",
    )


ASSEMBLYAI = AssemblyAI()


class SessionState(BaseSettings):
    CHAT_SESSION_PATH: Path = Path("chat_session.json")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="SESSION_",
    )


SESSION = SessionState()


class Bluesky(BaseSettings):
    USERNAME: str
    PASSWORD: str
    EMAIL: str

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="BLUESKY_",
    )


BLUESKY = Bluesky()


class Confluence(BaseSettings):
    API_TOKEN: str
    EMAIL: str
    URL: str

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="CONFLUENCE_",
    )


CONFLUENCE = Confluence()


class Redis(BaseSettings):
    URL: str = "redis://localhost:6379/0"
    DB: str = "mcp"
    PASSWORD: str = "redispassword"
    PORT: int = 6379

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="REDIS_",
    )


REDIS = Redis()


class Celery(BaseSettings):
    BROKER_URL: Optional[str] = None  # Defaults to Redis URL if None
    BACKEND_URL: Optional[str] = None  # Defaults to Redis URL if None
    APP_NAME: str = "mcp_scheduler"
    RESULT_EXPIRES: int = 3600  # 1 hour
    TASK_SERIALIZER: str = "json"
    RESULT_SERIALIZER: str = "json"
    ACCEPT_CONTENT: List[str] = ["json"]
    TIMEZONE: str = "UTC"
    ENABLE_UTC: bool = True

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="CELERY_",
    )

    def get_broker_url(self) -> str:
        """Return broker URL, defaulting to Redis URL if not specified."""
        return self.BROKER_URL or REDIS.URL

    def get_backend_url(self) -> str:
        """Return backend URL, defaulting to Redis URL if not specified."""
        return self.BACKEND_URL or REDIS.URL


CELERY = Celery()


class Flower(BaseSettings):
    BROKER_API: str = REDIS.URL
    ADDRESS: str = "0.0.0.0"
    PORT: int = 5555
    URL_PREFIX: str = ""
    BASIC_AUTH: str = ""  # Format: user:password
    MAX_TASKS: int = 10000
    DB: str = "flower.db"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="FLOWER_",
    )


FLOWER = Flower()
