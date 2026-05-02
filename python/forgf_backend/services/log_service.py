"""SQLite-backed logging for verification attempts."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class AttemptLogRecord:
    status: str
    access_granted: bool
    ip_address: str
    device_name: str
    browser_name: str
    os_name: str
    user_agent: str
    message: str
    distance: float | None
    threshold: float | None


@dataclass(slots=True)
class FailedSessionRecord:
    session_id: str
    reason: str
    message: str
    verify_requests: int
    unknown_streak_peak: int
    match_streak_peak: int
    session_seconds: float
    ip_address: str
    device_name: str
    browser_name: str
    os_name: str
    user_agent: str


def initialize_log_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS verification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                access_granted INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                device_name TEXT NOT NULL,
                browser_name TEXT NOT NULL,
                os_name TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                message TEXT NOT NULL,
                distance REAL,
                threshold REAL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS failed_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                session_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                message TEXT NOT NULL,
                verify_requests INTEGER NOT NULL,
                unknown_streak_peak INTEGER NOT NULL,
                match_streak_peak INTEGER NOT NULL,
                session_seconds REAL NOT NULL,
                ip_address TEXT NOT NULL,
                device_name TEXT NOT NULL,
                browser_name TEXT NOT NULL,
                os_name TEXT NOT NULL,
                user_agent TEXT NOT NULL
            )
            """
        )
        connection.commit()


def log_verification_attempt(database_path: Path, record: AttemptLogRecord) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO verification_logs (
                created_at,
                status,
                access_granted,
                ip_address,
                device_name,
                browser_name,
                os_name,
                user_agent,
                message,
                distance,
                threshold
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                record.status,
                int(record.access_granted),
                record.ip_address,
                record.device_name,
                record.browser_name,
                record.os_name,
                record.user_agent,
                record.message,
                record.distance,
                record.threshold,
            ),
        )
        connection.commit()


def log_failed_session(database_path: Path, record: FailedSessionRecord) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO failed_sessions (
                created_at,
                session_id,
                reason,
                message,
                verify_requests,
                unknown_streak_peak,
                match_streak_peak,
                session_seconds,
                ip_address,
                device_name,
                browser_name,
                os_name,
                user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                record.session_id,
                record.reason,
                record.message,
                record.verify_requests,
                record.unknown_streak_peak,
                record.match_streak_peak,
                record.session_seconds,
                record.ip_address,
                record.device_name,
                record.browser_name,
                record.os_name,
                record.user_agent,
            ),
        )
        connection.commit()


def fetch_recent_logs(database_path: Path, limit: int) -> list[dict[str, object]]:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                id,
                created_at,
                status,
                access_granted,
                ip_address,
                device_name,
                browser_name,
                os_name,
                user_agent,
                message,
                distance,
                threshold
            FROM verification_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def fetch_recent_failed_sessions(database_path: Path, limit: int) -> list[dict[str, object]]:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                id,
                created_at,
                session_id,
                reason,
                message,
                verify_requests,
                unknown_streak_peak,
                match_streak_peak,
                session_seconds,
                ip_address,
                device_name,
                browser_name,
                os_name,
                user_agent
            FROM failed_sessions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def fetch_log_summary(database_path: Path) -> dict[str, int]:
    with sqlite3.connect(database_path) as connection:
        total = connection.execute("SELECT COUNT(*) FROM verification_logs").fetchone()[0]
        matches = connection.execute(
            "SELECT COUNT(*) FROM verification_logs WHERE access_granted = 1"
        ).fetchone()[0]
        unknown = connection.execute(
            "SELECT COUNT(*) FROM verification_logs WHERE status = 'unknown'"
        ).fetchone()[0]
        no_face = connection.execute(
            "SELECT COUNT(*) FROM verification_logs WHERE status = 'no_face'"
        ).fetchone()[0]
        multiple_faces = connection.execute(
            "SELECT COUNT(*) FROM verification_logs WHERE status = 'multiple_faces'"
        ).fetchone()[0]
        failed_sessions = connection.execute(
            "SELECT COUNT(*) FROM failed_sessions"
        ).fetchone()[0]

    return {
        "total_attempts": total,
        "matches": matches,
        "unknown": unknown,
        "no_face": no_face,
        "multiple_faces": multiple_faces,
        "failed_sessions": failed_sessions,
    }


def delete_log_entry(database_path: Path, log_id: int) -> bool:
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            "DELETE FROM verification_logs WHERE id = ?",
            (log_id,),
        )
        connection.commit()

    return cursor.rowcount > 0


def delete_failed_session_entry(database_path: Path, log_id: int) -> bool:
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            "DELETE FROM failed_sessions WHERE id = ?",
            (log_id,),
        )
        connection.commit()

    return cursor.rowcount > 0


def clear_logs(database_path: Path) -> int:
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute("DELETE FROM verification_logs")
        failed_cursor = connection.execute("DELETE FROM failed_sessions")
        connection.commit()

    return cursor.rowcount + failed_cursor.rowcount
