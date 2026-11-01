from contextlib import asynccontextmanager
import os
import re
import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.api import api_router
from app.core.config import get_settings
from app.core.database import Base, engine

settings = get_settings()


def _ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "profiles" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("profiles")}
    if "birthday" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE profiles ADD COLUMN birthday VARCHAR(40) DEFAULT '2002-01-01'")
            )


def _cors_regex() -> str | None:
    pattern = (settings.cors_origin_regex or "").strip()
    if not pattern:
        return None
    try:
        re.compile(pattern)
    except re.error:
        return None
    return pattern


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    # Vercel cold starts cannot wait on DDL against Neon.
    if not os.getenv("VERCEL"):
        try:
            _ensure_schema()
        except Exception as exc:
            print(f"schema init skipped: {exc}")
    yield


settings.upload_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=_cors_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.mount(
    "/media",
    StaticFiles(directory=str(settings.upload_dir), check_dir=False),
    name="media",
)


@app.exception_handler(Exception)
async def unhandled(_request: Request, exc: Exception):
    if isinstance(exc, (HTTPException, RequestValidationError)):
        raise exc
    print(traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})


@app.get("/")
def root():
    return {
        "status": "ok",
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
