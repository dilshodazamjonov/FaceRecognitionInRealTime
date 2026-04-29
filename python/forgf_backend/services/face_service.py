"""Verification services that bridge HTTP uploads to the face engine."""

from __future__ import annotations

from ..config import AppConfig
from ..runtime import ensure_python_root_on_path
from ..services.log_service import AttemptLogRecord, log_verification_attempt
from ..services.reference_service import require_reference
from ..utils.client import ClientMeta
from ..utils.errors import ApiError

ensure_python_root_on_path()

from face_access_app.face_pipeline import verify_frame_against_reference  # noqa: E402


def verify_frame(
    config: AppConfig,
    frame,
    client_meta: ClientMeta,
) -> dict[str, object]:
    reference_data = require_reference(config)

    try:
        result = verify_frame_against_reference(
            frame,
            reference_data,
            max_dimension=config.max_inference_dimension,
        )
    except Exception as exc:
        raise ApiError(500, "verification_failed", "Face verification failed.") from exc

    result_dict = result.to_dict()
    log_verification_attempt(
        config.database_path,
        AttemptLogRecord(
            status=result_dict["status"],
            access_granted=bool(result_dict["access_granted"]),
            ip_address=client_meta.ip_address,
            device_name=client_meta.device_name,
            browser_name=client_meta.browser_name,
            os_name=client_meta.os_name,
            user_agent=client_meta.user_agent,
            message=result_dict["message"] or "",
            distance=result_dict["distance"],
            threshold=result_dict["threshold"],
        ),
    )
    return result_dict
