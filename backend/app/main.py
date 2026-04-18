from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import build_health_payload, router as api_router
from .core.config import Settings, get_settings
from .core.exceptions import AppError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def ensure_storage_directories(settings: Settings) -> None:
    for directory in (settings.upload_dir, settings.static_dir, settings.temp_dir):
        directory.mkdir(parents=True, exist_ok=True)


async def cleanup_old_files(settings: Settings) -> None:
    while True:
        cutoff_time = datetime.now() - timedelta(hours=settings.max_file_age_hours)
        try:
            for directory in (settings.upload_dir, settings.static_dir, settings.temp_dir):
                for file_path in directory.glob("*"):
                    if file_path.is_file():
                        modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if modified_at < cutoff_time:
                            file_path.unlink(missing_ok=True)
                            logger.info("Removed expired file: %s", file_path)
        except Exception:
            logger.exception("Background cleanup failed")

        await asyncio.sleep(settings.cleanup_interval_seconds)


def create_app() -> FastAPI:
    settings = get_settings()
    ensure_storage_directories(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        cleanup_task = asyncio.create_task(cleanup_old_files(settings))
        try:
            yield
        finally:
            cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await cleanup_task

    app = FastAPI(
        title=settings.app_name,
        description="Backend API for dental X-ray analysis and reporting.",
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
    app.include_router(api_router, prefix="/api")

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, object]:
        return {
            "service": settings.app_name,
            "status": "ok",
            "health": "/health",
            "docs": "/docs",
        }

    @app.get("/health", include_in_schema=False)
    async def health_check() -> dict[str, object]:
        return build_health_payload(settings)

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )

    return app


app = create_app()
