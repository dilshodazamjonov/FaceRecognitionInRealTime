"""Client metadata helpers for logging and admin views."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request


@dataclass(slots=True)
class ClientMeta:
    ip_address: str
    user_agent: str
    device_name: str
    browser_name: str
    os_name: str


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def _detect_browser(user_agent: str) -> str:
    ua = user_agent.lower()
    if "edg/" in ua:
        return "Edge"
    if "chrome/" in ua and "edg/" not in ua:
        return "Chrome"
    if "safari/" in ua and "chrome/" not in ua:
        return "Safari"
    if "firefox/" in ua:
        return "Firefox"
    if "opr/" in ua or "opera" in ua:
        return "Opera"
    return "Unknown Browser"


def _detect_os(user_agent: str) -> str:
    ua = user_agent.lower()
    if "iphone" in ua or "ipad" in ua or "ios" in ua:
        return "iOS"
    if "android" in ua:
        return "Android"
    if "windows" in ua:
        return "Windows"
    if "mac os x" in ua or "macintosh" in ua:
        return "macOS"
    if "linux" in ua:
        return "Linux"
    return "Unknown OS"


def _detect_device_name(user_agent: str) -> str:
    ua = user_agent.lower()
    if "ipad" in ua:
        return "iPad"
    if "iphone" in ua:
        return "iPhone"
    if "android" in ua and "mobile" in ua:
        return "Android Phone"
    if "android" in ua:
        return "Android Tablet"
    if "windows" in ua:
        return "Windows Device"
    if "macintosh" in ua or "mac os x" in ua:
        return "Mac Device"
    if "linux" in ua:
        return "Linux Device"
    return "Unknown Device"


def extract_client_meta(request: Request) -> ClientMeta:
    user_agent = request.headers.get("user-agent", "")
    browser_name = _detect_browser(user_agent)
    os_name = _detect_os(user_agent)
    device_name = _detect_device_name(user_agent)

    return ClientMeta(
        ip_address=get_client_ip(request),
        user_agent=user_agent,
        device_name=f"{device_name} / {browser_name}",
        browser_name=browser_name,
        os_name=os_name,
    )

