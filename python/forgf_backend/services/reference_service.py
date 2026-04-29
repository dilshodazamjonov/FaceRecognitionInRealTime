"""Reference enrollment and status services."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..config import AppConfig
from ..runtime import ensure_python_root_on_path
from ..utils.errors import ApiError

ensure_python_root_on_path()

from face_access_app.enroll import enroll_reference_from_image_source  # noqa: E402
from face_access_app.face_pipeline import (  # noqa: E402
    DEFAULT_MATCH_THRESHOLD,
    resize_image_for_inference,
)
from face_access_app.storage import StorageError, load_reference  # noqa: E402

_REFERENCE_CACHE: dict[str, object] = {
    "path": None,
    "mtime": None,
    "reference": None,
}


def get_reference_status(config: AppConfig) -> dict[str, object]:
    if not config.reference_path.exists():
        return {"reference_exists": False}

    try:
        reference_data = load_reference(config.reference_path)
    except StorageError as exc:
        raise ApiError(500, "reference_load_failed", str(exc)) from exc

    return {
        "reference_exists": True,
        "label": reference_data.label,
        "source_image_path": reference_data.source_image_path,
        "threshold": reference_data.threshold,
        "model_name": reference_data.model_name,
        "detector_backend": reference_data.detector_backend,
    }


def require_reference(config: AppConfig):
    reference_path = config.reference_path
    try:
        current_mtime = reference_path.stat().st_mtime_ns
    except FileNotFoundError as exc:
        raise ApiError(
            409,
            "reference_missing",
            "No enrolled reference exists. Enroll a reference image first.",
        ) from exc

    if (
        _REFERENCE_CACHE["path"] == str(reference_path)
        and _REFERENCE_CACHE["mtime"] == current_mtime
        and _REFERENCE_CACHE["reference"] is not None
    ):
        return _REFERENCE_CACHE["reference"]

    try:
        reference = load_reference(reference_path)
    except StorageError as exc:
        raise ApiError(
            409,
            "reference_missing",
            "No enrolled reference exists. Enroll a reference image first.",
        ) from exc

    _REFERENCE_CACHE["path"] = str(reference_path)
    _REFERENCE_CACHE["mtime"] = current_mtime
    _REFERENCE_CACHE["reference"] = reference
    return reference


def enroll_reference_image(
    config: AppConfig,
    image: np.ndarray,
    source_name: str,
    label: str,
    threshold: float | None,
) -> Path:
    active_threshold = float(threshold if threshold is not None else DEFAULT_MATCH_THRESHOLD)
    resized_image, _ = resize_image_for_inference(
        image,
        max_dimension=config.max_inference_dimension,
    )

    try:
        return enroll_reference_from_image_source(
            image_source=resized_image,
            source_image_path=source_name,
            label=label,
            output_path=config.reference_path,
            threshold=active_threshold,
        )
    except FileNotFoundError as exc:
        raise ApiError(400, "image_not_found", str(exc)) from exc
    except Exception as exc:
        message = str(exc)
        error_code = "enrollment_failed"
        status_code = 400
        if "No face detected" in message:
            error_code = "no_face_detected"
        elif "Expected exactly one face" in message:
            error_code = "multiple_faces_detected"
        else:
            status_code = 500
        raise ApiError(status_code, error_code, message) from exc
