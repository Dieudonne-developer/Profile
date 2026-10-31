from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Portfolio API"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/portfolio"
    database_url_unpooled: str = ""
    secret_key: str = "dev-only-change-me"
    access_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    public_api_url: str = "http://127.0.0.1:8000"
    public_app_url: str = "http://127.0.0.1:5173"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )
    cors_origin_regex: str = ""
    upload_dir: Path = ROOT / "app" / "static" / "uploads"
    ml_backend_url: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
