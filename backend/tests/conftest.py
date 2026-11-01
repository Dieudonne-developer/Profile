import os
from pathlib import Path

TEST_DB = Path(__file__).resolve().parent / "testdb.sqlite"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["DATABASE_URL_UNPOOLED"] = ""
os.environ["SECRET_KEY"] = "test-secret-key-must-be-32-bytes"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ALLOW_REGISTRATION"] = "true"

from app.core.config import get_settings

get_settings.cache_clear()
get_settings()
