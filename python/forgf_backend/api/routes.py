"""HTTP routes for the ForGF backend."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..config import get_config
from ..schemas.requests import FailedAttemptRequest
from ..schemas.responses import (
    ActionResponse,
    EnrollResponse,
    ErrorResponse,
    HealthResponse,
    ReferenceStatusResponse,
    VerificationResponse,
)
from ..services.face_service import verify_frame
from ..services.log_service import (
    FailedSessionRecord,
    clear_logs,
    delete_failed_session_entry,
    delete_log_entry,
    fetch_log_summary,
    fetch_recent_failed_sessions,
    fetch_recent_logs,
    log_failed_session,
)
from ..services.reference_service import enroll_reference_image, get_reference_status
from ..utils.client import extract_client_meta
from ..utils.errors import ApiError
from ..utils.images import read_and_decode_upload


router = APIRouter()
config = get_config()
templates = Jinja2Templates(directory=str(config.template_dir))
ADMIN_COOKIE_NAME = "forgf_admin_auth"


def _valid_admin_secrets() -> set[str]:
    return {config.admin_password, config.admin_token}


def _extract_admin_secret(request: Request, token: str | None = None) -> str | None:
    cookie_secret = request.cookies.get(ADMIN_COOKIE_NAME)
    header_secret = request.headers.get("x-admin-token")
    return cookie_secret or token or header_secret


def _is_valid_admin_secret(secret: str | None) -> bool:
    return bool(secret) and secret in _valid_admin_secrets()


def _require_admin(request: Request, token: str | None = None) -> None:
    if not _is_valid_admin_secret(_extract_admin_secret(request, token)):
        raise ApiError(403, "forbidden", "Admin access requires a valid password.")


def _set_admin_cookie(response: RedirectResponse) -> None:
    response.set_cookie(
        key=ADMIN_COOKIE_NAME,
        value=config.admin_password,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 30,
    )


def _clear_admin_cookie(response: RedirectResponse) -> None:
    response.delete_cookie(key=ADMIN_COOKIE_NAME, httponly=True, samesite="lax")


def _admin_logs_url(request: Request, notice: str | None = None) -> str:
    target = str(request.url_for("admin_logs"))
    if not notice:
        return target
    return f"{target}?{urlencode({'notice': notice})}"


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
    active_reference_path, labeled_reference_path = enroll_reference_image(
        config=config,
        image=decoded_image.image,
        source_name=decoded_image.filename,
        label=label,
        threshold=threshold,
    )

    return EnrollResponse(
        success=True,
        label=label,
        reference_path=str(active_reference_path),
        labeled_reference_path=str(labeled_reference_path),
        threshold=float(get_reference_status(config)["threshold"]),
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


@router.post(
    "/attempts/failed",
    response_model=ActionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def log_failed_attempt(request: Request, payload: FailedAttemptRequest) -> ActionResponse:
    client_meta = extract_client_meta(request)
    log_failed_session(
        config.database_path,
        FailedSessionRecord(
            session_id=payload.session_id,
            reason=payload.reason,
            message=payload.message,
            verify_requests=payload.verify_requests,
            unknown_streak_peak=payload.unknown_streak_peak,
            match_streak_peak=payload.match_streak_peak,
            session_seconds=payload.session_seconds,
            ip_address=client_meta.ip_address,
            device_name=client_meta.device_name,
            browser_name=client_meta.browser_name,
            os_name=client_meta.os_name,
            user_agent=client_meta.user_agent,
        ),
    )
    return ActionResponse(success=True, message="Failed attempt recorded.")


@router.get("/admin", include_in_schema=False)
async def admin_root(request: Request) -> RedirectResponse:
    destination = request.url_for("admin_logs") if _is_valid_admin_secret(_extract_admin_secret(request)) else request.url_for("admin_login")
    return RedirectResponse(str(destination), status_code=303)


@router.get("/admin/login", response_class=HTMLResponse, include_in_schema=False)
async def admin_login(
    request: Request,
    error: str | None = Query(default=None),
    notice: str | None = Query(default=None),
) -> HTMLResponse:
    if _is_valid_admin_secret(_extract_admin_secret(request)):
        return RedirectResponse(str(request.url_for("admin_logs")), status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={
            "error": error,
            "notice": notice,
        },
    )


@router.post("/admin/login", include_in_schema=False)
async def admin_login_submit(
    request: Request,
    password: str = Form(...),
) -> RedirectResponse:
    normalized = password.strip()
    if normalized not in _valid_admin_secrets():
        return RedirectResponse(
            str(request.url_for("admin_login")) + "?error=Wrong+password",
            status_code=303,
        )

    response = RedirectResponse(str(request.url_for("admin_logs")), status_code=303)
    _set_admin_cookie(response)
    return response


@router.post("/admin/logout", include_in_schema=False)
async def admin_logout(request: Request) -> RedirectResponse:
    response = RedirectResponse(
        str(request.url_for("admin_login")) + "?notice=Logged+out",
        status_code=303,
    )
    _clear_admin_cookie(response)
    return response


@router.get("/admin/logs", response_class=HTMLResponse)
async def admin_logs(
    request: Request,
    token: str | None = Query(default=None),
    notice: str | None = Query(default=None),
) -> HTMLResponse:
    if not _is_valid_admin_secret(_extract_admin_secret(request, token)):
        return RedirectResponse(str(request.url_for("admin_login")), status_code=303)
    logs = fetch_recent_logs(config.database_path, config.log_limit)
    failed_sessions = fetch_recent_failed_sessions(config.database_path, max(10, config.log_limit // 2))
    summary = fetch_log_summary(config.database_path)

    return templates.TemplateResponse(
        request=request,
        name="admin_logs.html",
        context={
            "summary": summary,
            "logs": logs,
            "failed_sessions": failed_sessions,
            "log_limit": config.log_limit,
            "notice": notice,
        },
    )


@router.post("/admin/logs/{log_id}/delete")
async def delete_admin_log(
    request: Request,
    log_id: int,
    token: str | None = Form(default=None),
) -> RedirectResponse:
    _require_admin(request, token)
    deleted = delete_log_entry(config.database_path, log_id)
    notice = "Log entry deleted." if deleted else "Log entry not found."
    return RedirectResponse(_admin_logs_url(request, notice), status_code=303)


@router.post("/admin/failed-sessions/{log_id}/delete")
async def delete_failed_session(
    request: Request,
    log_id: int,
    token: str | None = Form(default=None),
) -> RedirectResponse:
    _require_admin(request, token)
    deleted = delete_failed_session_entry(config.database_path, log_id)
    notice = "Failed session deleted." if deleted else "Failed session not found."
    return RedirectResponse(_admin_logs_url(request, notice), status_code=303)


@router.post("/admin/logs/clear")
async def clear_admin_logs(
    request: Request,
    token: str | None = Form(default=None),
) -> RedirectResponse:
    _require_admin(request, token)
    deleted_count = clear_logs(config.database_path)
    label = "entry" if deleted_count == 1 else "entries"
    notice = f"Deleted {deleted_count} log {label}."
    return RedirectResponse(_admin_logs_url(request, notice), status_code=303)
