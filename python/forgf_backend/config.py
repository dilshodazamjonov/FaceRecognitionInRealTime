"""Configuration for the ForGF backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .runtime import PYTHON_ROOT


def _parse_bool(raw_value: str | None, default: bool) -> bool:
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_origins(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return ("http://localhost:3000", "http://127.0.0.1:3000")
    return tuple(origin.strip() for origin in raw_value.split(",") if origin.strip())


@dataclass(frozen=True, slots=True)
class AppConfig:
    app_name: str
    host: str
    port: int
    debug: bool
    allowed_origins: tuple[str, ...]
    max_upload_bytes: int
    reference_path: Path
    database_path: Path
    admin_token: str
    log_limit: int
    template_dir: Path
    max_inference_dimension: int
    warmup_models: bool


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    max_upload_mb = int(os.getenv("FORGF_MAX_UPLOAD_MB", "5"))
    reference_path_raw = os.getenv("FORGF_REFERENCE_PATH")
    reference_path = (
        Path(reference_path_raw)
        if reference_path_raw
        else PYTHON_ROOT / "face_access_app" / "references" / "girlfriend_reference.npz"
    )

    return AppConfig(
        app_name="ForGF Backend",
        host=os.getenv("FORGF_HOST", "127.0.0.1"),
        port=int(os.getenv("FORGF_PORT", "8000")),
        debug=_parse_bool(os.getenv("FORGF_DEBUG"), default=False),
        allowed_origins=_parse_origins(os.getenv("FORGF_ALLOWED_ORIGINS")),
        max_upload_bytes=max_upload_mb * 1024 * 1024,
        reference_path=reference_path,
        database_path=PYTHON_ROOT / "forgf_backend" / "data" / "forgf_logs.sqlite3",
        admin_token=os.getenv("FORGF_ADMIN_TOKEN", "change-me-admin-token"),
        log_limit=int(os.getenv("FORGF_LOG_LIMIT", "200")),
        template_dir=PYTHON_ROOT / "forgf_backend" / "templates",
        max_inference_dimension=int(os.getenv("FORGF_MAX_INFERENCE_DIMENSION", "640")),
        warmup_models=_parse_bool(os.getenv("FORGF_WARMUP_MODELS"), default=True),
    )
