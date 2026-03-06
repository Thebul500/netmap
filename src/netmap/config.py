"""Application configuration from environment variables."""

import secrets

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    database_url: str = "postgresql+asyncpg://localhost:5432/netmap"
    secret_key: str = secrets.token_hex(32)
    access_token_expire_minutes: int = 30
    debug: bool = False

    model_config = {"env_prefix": "NETMAP_"}


settings = Settings()
