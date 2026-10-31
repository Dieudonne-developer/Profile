from collections.abc import Generator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def normalize_database_url(url: str) -> str:
    cleaned = (url or "").strip().strip('"').strip("'")
    if not cleaned:
        raise RuntimeError(
            "DATABASE_URL is empty. Set it in backend/.env "
            "(Neon: postgresql://... or postgresql+psycopg://...)."
        )
    if cleaned.startswith("sqlite"):
        return cleaned
    if cleaned.startswith("postgres://"):
        cleaned = "postgresql://" + cleaned[len("postgres://") :]
    scheme, remainder = cleaned.split("://", 1)
    if scheme == "postgresql":
        cleaned = "postgresql+psycopg://" + remainder
    if "neon.tech" in cleaned:
        parts = urlsplit(cleaned)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query.setdefault("sslmode", "require")
        cleaned = urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
        )
    return cleaned


def application_database_url() -> str:
    return normalize_database_url(get_settings().database_url)


def alembic_database_url() -> str:
    settings = get_settings()
    return normalize_database_url(settings.database_url_unpooled or settings.database_url)


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}

    parsed = make_url(url)
    host = (parsed.host or "").lower()
    is_neon = host.endswith("neon.tech")
    timeout = 30 if is_neon else 10
    kwargs: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {"connect_timeout": timeout},
    }
    if "-pooler." in host:
        kwargs["poolclass"] = NullPool
    return kwargs


DATABASE_URL = application_database_url()
engine = create_engine(DATABASE_URL, **_engine_kwargs(DATABASE_URL))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
