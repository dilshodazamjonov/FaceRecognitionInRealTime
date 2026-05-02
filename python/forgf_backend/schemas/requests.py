"""Request schemas for the ForGF backend."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FailedAttemptRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=1, max_length=60)
    message: str = Field(min_length=1, max_length=280)
    verify_requests: int = Field(default=0, ge=0, le=500)
    unknown_streak_peak: int = Field(default=0, ge=0, le=100)
    match_streak_peak: int = Field(default=0, ge=0, le=100)
    session_seconds: float = Field(default=0.0, ge=0.0, le=3600.0)
