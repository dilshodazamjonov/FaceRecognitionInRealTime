"""HTTP routes for the ForGF backend."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..config import get_config
from ..schemas.responses import (
    EnrollResponse,
    ErrorResponse,
    HealthResponse,
    ReferenceStatusResponse,
    VerificationResponse,
)
from ..services.face_service import verify_frame
from ..services.log_service import clear_logs, delete_log_entry, fetch_log_summary, fetch_recent_logs
from ..services.reference_service import enroll_reference_image, get_reference_status
from ..utils.client import extract_client_meta
from ..utils.errors import ApiError
from ..utils.images import read_and_decode_upload


router = APIRouter()
config = get_config()
templates = Jinja2Templates(directory=str(config.template_dir))


def _require_admin(request: Request, token: str | None) -> None:
    header_token = request.headers.get("x-admin-token")
    active_token = token or header_token
    if active_token != config.admin_token:
        raise ApiError(403, "forbidden", "Admin access requires a valid token.")


def _admin_logs_url(request: Request, token: str, notice: str | None = None) -> str:
    params: dict[str, str] = {"token": token}
    if notice:
        params["notice"] = notice
    return f"{request.url_for('admin_logs')}?{urlencode(params)}"


@router.get("/", response_model=HealthResponse, response_model_exclude_none=True)
async def root() -> HealthResponse:
    reference_status = get_reference_status(config)
    return HealthResponse(
        status="ok",
        service=config.app_name,
        reference_exists=bool(reference_status["reference_exists"]),
    )


@router.get("/health", response_model=HealthResponse, response_model_exclude_none=True)
async def health() -> HealthResponse:
    reference_status = get_reference_status(config)
    return HealthResponse(
        status="ok",
        service=config.app_name,
        reference_exists=bool(reference_status["reference_exists"]),
    )


@router.get("/reference", response_model=ReferenceStatusResponse)
async def reference_status() -> ReferenceStatusResponse:
    return ReferenceStatusResponse(**get_reference_status(config))


@router.post(
    "/enroll",
    response_model=EnrollResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def enroll(
    image: UploadFile,
    label: str = Form("girlfriend"),
    threshold: float | None = Form(None),
) -> EnrollResponse:
    decoded_image = await read_and_decode_upload(image, config.max_upload_bytes)
    saved_path = enroll_reference_image(
        config=config,
        image=decoded_image.image,
        source_name=decoded_image.filename,
        label=label,
        threshold=threshold,
    )

    return EnrollResponse(
        success=True,
        label=label,
        reference_path=str(saved_path),
        threshold=float(threshold if threshold is not None else get_reference_status(config)["threshold"]),
    )


@router.post(
    "/verify",
    response_model=VerificationResponse,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def verify(request: Request, image: UploadFile) -> VerificationResponse:
    decoded_image = await read_and_decode_upload(image, config.max_upload_bytes)
    client_meta = extract_client_meta(request)
    result = verify_frame(config=config, frame=decoded_image.image, client_meta=client_meta)
    return VerificationResponse(**result)


@router.get("/admin/logs", response_class=HTMLResponse)
async def admin_logs(
    request: Request,
    token: str | None = Query(default=None),
    notice: str | None = Query(default=None),
) -> HTMLResponse:
    _require_admin(request, token)
    active_token = token or request.headers.get("x-admin-token") or ""
    logs = fetch_recent_logs(config.database_path, config.log_limit)
    summary = fetch_log_summary(config.database_path)

    return templates.TemplateResponse(
        request=request,
        name="admin_logs.html",
        context={
            "summary": summary,
            "logs": logs,
            "log_limit": config.log_limit,
            "admin_token": active_token,
            "notice": notice,
        },
    )


@router.post("/admin/logs/{log_id}/delete")
async def delete_admin_log(
    request: Request,
    log_id: int,
    token: str = Form(...),
) -> RedirectResponse:
    _require_admin(request, token)
    deleted = delete_log_entry(config.database_path, log_id)
    notice = "Log entry deleted." if deleted else "Log entry not found."
    return RedirectResponse(_admin_logs_url(request, token, notice), status_code=303)


@router.post("/admin/logs/clear")
async def clear_admin_logs(
    request: Request,
    token: str = Form(...),
) -> RedirectResponse:
    _require_admin(request, token)
    deleted_count = clear_logs(config.database_path)
    label = "entry" if deleted_count == 1 else "entries"
    notice = f"Deleted {deleted_count} log {label}."
    return RedirectResponse(_admin_logs_url(request, token, notice), status_code=303)
