"""Image upload validation and decoding helpers."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from fastapi import UploadFile

from .errors import ApiError


ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
}


@dataclass(slots=True)
class DecodedImage:
    image: np.ndarray
    filename: str
    content_type: str
    size_bytes: int


async def read_and_decode_upload(
    upload: UploadFile,
    max_upload_bytes: int,
) -> DecodedImage:
    if upload.filename is None:
        raise ApiError(400, "missing_filename", "Uploaded image must include a filename.")

    content_type = (upload.content_type or "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise ApiError(
            400,
            "invalid_content_type",
            f"Unsupported image content type: {upload.content_type}",
        )

    raw_bytes = await upload.read()
    size_bytes = len(raw_bytes)
    if size_bytes == 0:
        raise ApiError(400, "empty_upload", "Uploaded image file is empty.")
    if size_bytes > max_upload_bytes:
        raise ApiError(
            400,
            "file_too_large",
            f"Uploaded image exceeds the {max_upload_bytes} byte limit.",
        )

    buffer = np.frombuffer(raw_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ApiError(400, "invalid_image", "Uploaded file could not be decoded as an image.")

    return DecodedImage(
        image=image,
        filename=upload.filename,
        content_type=content_type or "application/octet-stream",
        size_bytes=size_bytes,
    )

