from app.core.database import normalize_database_url


def test_normalize_neon_postgres_url():
    raw = (
        '"postgresql://owner:secret@ep-example-pooler.c-4.us-west-2.aws.neon.tech/neondb'
        '?channel_binding=require"'
    )
    url = normalize_database_url(raw)
    assert url.startswith("postgresql+psycopg://")
    assert "sslmode=require" in url
    assert "neon.tech" in url
    assert "channel_binding" not in url
    assert not url.startswith('"')


def test_normalize_sqlite_unchanged():
    assert normalize_database_url("sqlite:///./app.db") == "sqlite:///./app.db"
