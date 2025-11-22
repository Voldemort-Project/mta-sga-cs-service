"""Application configuration using Pydantic Settings"""
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
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

    # Keycloak
    keycloak_server_url: str = "http://localhost:8080"
    keycloak_realm: str = "master"
    keycloak_client_id: str = "sga-cs-service"
    keycloak_client_secret: str = ""
    keycloak_verify_ssl: bool = True

    # JWT Settings
    jwt_algorithm: str = "RS256"
    jwt_audience: str | None = None  # Optional, will use client_id if not set

    # WAHA (WhatsApp HTTP API)
    waha_host: str = "http://localhost:3000"
    waha_api_path: str = "/api/sendText"
    waha_session: str = "default"
    waha_api_key: str = ""  # X-API-Key for WAHA authentication

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def model_post_init(self, __context) -> None:
        """Clean database URL of asyncpg-incompatible parameters"""
        # Remove psycopg2-specific parameters that asyncpg doesn't support
        self.database_url = self._clean_asyncpg_url(self.database_url)

    @staticmethod
    def _clean_asyncpg_url(url: str) -> str:
        """Remove query parameters not supported by asyncpg"""
        if "+asyncpg" not in url:
            return url

        parsed = urlparse(url)
        if not parsed.query:
            return url

        # Parse query parameters
        params = parse_qs(parsed.query)

        # Remove asyncpg-incompatible parameters
        unsupported = ["sslmode", "channel_binding"]
        for param in unsupported:
            params.pop(param, None)

        # Rebuild query string
        new_query = urlencode(params, doseq=True) if params else ""

        # Rebuild URL
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic migrations"""
        return self.database_url.replace("+asyncpg", "")


settings = Settings()
