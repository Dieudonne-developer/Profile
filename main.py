"""ASGI entry so `uvicorn main:app --reload` works from the repo root."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent / "backend"
backend_path = str(_BACKEND)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app  # noqa: E402

__all__ = ["app"]
