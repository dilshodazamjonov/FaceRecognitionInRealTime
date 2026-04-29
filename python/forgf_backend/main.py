"""FastAPI app entry point for the ForGF backend."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import get_config
from .services.log_service import initialize_log_database
from .runtime import ensure_python_root_on_path
from .utils.errors import install_exception_handlers

ensure_python_root_on_path()

from face_access_app.face_pipeline import warm_up_models  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    initialize_log_database(config.database_path)
    if config.warmup_models:
        warm_up_models()
    yield


def create_app() -> FastAPI:
    config = get_config()
    app = FastAPI(title=config.app_name, debug=config.debug, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    install_exception_handlers(app)
    return app


def main() -> None:
    config = get_config()
    uvicorn.run(
        "forgf_backend.main:create_app",
        factory=True,
        host=config.host,
        port=config.port,
        reload=config.debug,
    )


app = create_app()
