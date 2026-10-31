from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    _ensure_schema()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.mount("/media", StaticFiles(directory=settings.upload_dir), name="media")


@app.exception_handler(Exception)
async def unhandled(_request: Request, exc: Exception):
    if isinstance(exc, (HTTPException, RequestValidationError)):
        raise exc
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})


@app.get("/")
def root():
    return {
        "status": "ok",
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
