"""Application configuration using Pydantic Settings"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "sga-cs-service"
    app_version: str = "0.1.0"
    env: str = "development"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database - Neon PostgreSQL
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/cs_service"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600  # 1 hour - recommended for Neon
    db_echo: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic migrations"""
        return self.database_url.replace("+asyncpg", "")


settings = Settings()
