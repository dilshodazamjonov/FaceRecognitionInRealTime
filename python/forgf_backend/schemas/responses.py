"""Response schemas for the ForGF backend."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    reference_exists: bool


class ReferenceStatusResponse(BaseModel):
    reference_exists: bool
    label: str | None = None
    source_image_path: str | None = None
    threshold: float | None = None
    model_name: str | None = None
    detector_backend: str | None = None


class EnrollResponse(BaseModel):
    success: bool
    label: str
    reference_path: str
    threshold: float


class VerificationResponse(BaseModel):
    status: str
    matched: bool
    access_granted: bool
    label: str
    face_count: int
    distance: float | None = None
    threshold: float | None = None
    boxes: list[tuple[int, int, int, int]]
    message: str | None = None
    next_screen: str
    should_redirect: bool


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail

