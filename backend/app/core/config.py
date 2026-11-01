from functools import lru_cache
from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


def _default_upload_dir() -> Path:
    if os.getenv("VERCEL"):
        return Path("/tmp/portfolio-uploads")
    return ROOT / "app" / "static" / "uploads"


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
        "http://localhost:5174,http://127.0.0.1:5174,"
        "https://profile-zzeb.vercel.app"
    )
    cors_origin_regex: str = r"https://.*\.vercel\.app"
    upload_dir: Path = _default_upload_dir()
    ml_backend_url: str = ""
    allow_registration: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "ntarindwajean11@gmail.com"
    smtp_password: str = ""
    gmail_app_password: str = ""
    smtp_from: str = "ntarindwajean11@gmail.com"
    notify_email: str = "ntarindwajean11@gmail.com"

    def mail_password(self) -> str:
        return (self.smtp_password or self.gmail_app_password or "").replace(" ", "").strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
