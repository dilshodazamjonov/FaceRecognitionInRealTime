"""Shared face detection, embedding, and verification helpers."""

from __future__ import annotations

import logging
import os
import warnings
from contextlib import redirect_stderr
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any
import time

# Reduce TensorFlow / oneDNN startup noise before any model imports happen.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
warnings.filterwarnings(
    "ignore",
    message=r".*sparse_softmax_cross_entropy is deprecated.*",
)

import cv2
import numpy as np

with redirect_stderr(StringIO()):
    from deepface import DeepFace
    from retinaface import RetinaFace

logging.getLogger("tensorflow").setLevel(logging.ERROR)

try:
    from .storage import ReferenceData
except ImportError:  # pragma: no cover - supports direct script execution
    from storage import ReferenceData


MODEL_NAME = "ArcFace"
DETECTOR_BACKEND = "retinaface"
DISTANCE_METRIC = "cosine"
DEFAULT_MATCH_THRESHOLD = 0.50
DEFAULT_REQUIRED_CONSECUTIVE_MATCHES = 5
DEFAULT_MAX_INFERENCE_DIMENSION = 640
SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MATCH_SCREEN = "wishes"
FAIL_SCREEN = "not_found"
CAMERA_SCREEN = "camera"


class FacePipelineError(RuntimeError):
    """Raised when the image-to-embedding pipeline fails."""


class ImageLoadError(FacePipelineError):
    """Raised when an image cannot be loaded from disk."""


class NoFaceDetectedError(FacePipelineError):
    """Raised when no face is found in an image."""


class MultipleFacesDetectedError(FacePipelineError):
    """Raised when more than one face is found in an image."""


@dataclass(slots=True)
class EmbeddingResult:
    """Single-face embedding extraction result."""

    embedding: np.ndarray
    face_count: int
    boxes: list[tuple[int, int, int, int]]


@dataclass(slots=True)
class VerificationResult:
    """Structured verification result for image or live camera checks."""

    status: str
    matched: bool
    access_granted: bool
    label: str
    face_count: int
    distance: float | None = None
    threshold: float | None = None
    boxes: list[tuple[int, int, int, int]] | None = None
    message: str | None = None
    next_screen: str = CAMERA_SCREEN
    should_redirect: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "matched": self.matched,
            "access_granted": self.access_granted,
            "label": self.label,
            "face_count": self.face_count,
            "distance": self.distance,
            "threshold": self.threshold,
            "boxes": self.boxes or [],
            "message": self.message,
            "next_screen": self.next_screen,
            "should_redirect": self.should_redirect,
        }


def project_root() -> Path:
    """Return the repository root based on the module location."""

    return Path(__file__).resolve().parent.parent.parent


def default_data_dir() -> Path:
    """Return the default data directory used by v1 enrollment."""

    return project_root() / "data"


def find_first_image(data_dir: str | Path | None = None) -> Path:
    """Find the first supported image in the given directory."""

    search_dir = Path(data_dir) if data_dir else default_data_dir()
    if not search_dir.exists():
        raise FileNotFoundError(f"Data directory does not exist: {search_dir}")

    image_paths = sorted(
        path
        for path in search_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    )
    if not image_paths:
        raise FileNotFoundError(f"No supported images found in: {search_dir}")

    return image_paths[0]


def load_image(image_path: str | Path) -> np.ndarray:
    """Load an image from disk with basic validation."""

    candidate_path = Path(image_path)
    if not candidate_path.exists():
        raise ImageLoadError(f"Image path does not exist: {candidate_path}")

    image = cv2.imread(str(candidate_path))
    if image is None:
        raise ImageLoadError(f"Failed to read image: {candidate_path}")

    return image


def resize_image_for_inference(
    image: np.ndarray,
    max_dimension: int = DEFAULT_MAX_INFERENCE_DIMENSION,
) -> tuple[np.ndarray, float]:
    """Resize an image for faster inference while preserving aspect ratio."""

    if max_dimension <= 0:
        return image, 1.0

    height, width = image.shape[:2]
    current_max = max(height, width)
    if current_max <= max_dimension:
        return image, 1.0

    scale = max_dimension / float(current_max)
    resized = cv2.resize(
        image,
        (max(1, int(round(width * scale))), max(1, int(round(height * scale)))),
        interpolation=cv2.INTER_AREA,
    )
    return resized, scale


def detect_faces(image_source: str | Path | np.ndarray) -> list[dict[str, Any]]:
    """Detect faces with RetinaFace and normalize the response into a list."""

    try:
        raw_faces = RetinaFace.detect_faces(img_path=image_source)
    except Exception as exc:
        message = str(exc).lower()
        if "face could not be detected" in message or "faces could not be detected" in message:
            return []
        raise FacePipelineError("RetinaFace detection failed.") from exc

    if isinstance(raw_faces, dict):
        if not raw_faces:
            return []

        if "facial_area" in raw_faces:
            return [raw_faces]

        detections = []
        for key in sorted(raw_faces.keys()):
            candidate = raw_faces[key]
            if isinstance(candidate, dict) and "facial_area" in candidate:
                detections.append(candidate)
        return detections

    return []


def _normalize_box(face_payload: dict[str, Any]) -> tuple[int, int, int, int]:
    facial_area = face_payload.get("facial_area")
    if isinstance(facial_area, dict):
        x = int(facial_area.get("x", 0))
        y = int(facial_area.get("y", 0))
        w = int(facial_area.get("w", 0))
        h = int(facial_area.get("h", 0))
        return x, y, x + w, y + h

    if isinstance(facial_area, (list, tuple)) and len(facial_area) >= 4:
        return tuple(int(value) for value in facial_area[:4])

    raise FacePipelineError("Face detection payload did not include a valid facial area.")


def _extract_boxes(face_payloads: list[dict[str, Any]]) -> list[tuple[int, int, int, int]]:
    return [_normalize_box(payload) for payload in face_payloads]


def _rescale_boxes(
    boxes: list[tuple[int, int, int, int]],
    scale: float,
) -> list[tuple[int, int, int, int]]:
    if scale == 1.0:
        return boxes

    inverse_scale = 1.0 / scale
    return [
        tuple(int(round(value * inverse_scale)) for value in box)
        for box in boxes
    ]


def extract_embedding(
    image_source: str | Path | np.ndarray,
    model_name: str = MODEL_NAME,
    detector_backend: str = DETECTOR_BACKEND,
) -> np.ndarray:
    """Extract a single embedding from an image source."""

    try:
        representations = DeepFace.represent(
            img_path=image_source,
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=True,
            align=True,
            max_faces=1,
        )
    except Exception as exc:
        raise FacePipelineError("DeepFace embedding extraction failed.") from exc

    if not representations:
        raise FacePipelineError("DeepFace returned no embedding results.")

    embedding = np.asarray(representations[0]["embedding"], dtype=np.float32).reshape(-1)
    if embedding.size == 0:
        raise FacePipelineError("DeepFace returned an empty embedding.")

    return embedding


def extract_embedding_from_face_crop(
    image: np.ndarray,
    face_box: tuple[int, int, int, int],
    model_name: str = MODEL_NAME,
    padding_ratio: float = 0.12,
) -> np.ndarray:
    """Fallback embedding extraction using an already-detected face crop."""

    height, width = image.shape[:2]
    x1, y1, x2, y2 = face_box

    pad_x = int(round((x2 - x1) * padding_ratio))
    pad_y = int(round((y2 - y1) * padding_ratio))

    left = max(0, x1 - pad_x)
    top = max(0, y1 - pad_y)
    right = min(width, x2 + pad_x)
    bottom = min(height, y2 + pad_y)

    if left >= right or top >= bottom:
        raise FacePipelineError("Detected face crop was invalid.")

    face_crop = image[top:bottom, left:right]
    if face_crop.size == 0:
        raise FacePipelineError("Detected face crop was empty.")

    try:
        representations = DeepFace.represent(
            img_path=face_crop,
            model_name=model_name,
            detector_backend="skip",
            enforce_detection=False,
            align=False,
            max_faces=1,
        )
    except Exception as exc:
        raise FacePipelineError("DeepFace face-crop embedding extraction failed.") from exc

    if not representations:
        raise FacePipelineError("DeepFace returned no embedding results for the face crop.")

    embedding = np.asarray(representations[0]["embedding"], dtype=np.float32).reshape(-1)
    if embedding.size == 0:
        raise FacePipelineError("DeepFace returned an empty face-crop embedding.")

    return embedding


def extract_single_face_embedding(
    image_source: str | Path | np.ndarray,
    model_name: str = MODEL_NAME,
    detector_backend: str = DETECTOR_BACKEND,
) -> EmbeddingResult:
    """Detect exactly one face and return its embedding."""

    detections = detect_faces(image_source)
    face_count = len(detections)

    if face_count == 0:
        raise NoFaceDetectedError("No face detected. Expected exactly one face.")
    if face_count > 1:
        raise MultipleFacesDetectedError(
            f"Detected {face_count} faces. Expected exactly one face."
        )

    return EmbeddingResult(
        embedding=extract_embedding(
            image_source=image_source,
            model_name=model_name,
            detector_backend=detector_backend,
        ),
        face_count=face_count,
        boxes=_extract_boxes(detections),
    )


def cosine_distance(reference_embedding: np.ndarray, candidate_embedding: np.ndarray) -> float:
    """Compute cosine distance between two embeddings."""

    reference_vector = np.asarray(reference_embedding, dtype=np.float32).reshape(-1)
    candidate_vector = np.asarray(candidate_embedding, dtype=np.float32).reshape(-1)

    if reference_vector.size == 0 or candidate_vector.size == 0:
        raise FacePipelineError("Embedding comparison requires non-empty vectors.")
    if reference_vector.shape != candidate_vector.shape:
        raise FacePipelineError(
            "Embedding shapes do not match for comparison: "
            f"{reference_vector.shape} vs {candidate_vector.shape}"
        )

    reference_norm = float(np.linalg.norm(reference_vector))
    candidate_norm = float(np.linalg.norm(candidate_vector))
    if reference_norm == 0.0 or candidate_norm == 0.0:
        raise FacePipelineError("Embedding comparison failed because a vector norm was zero.")

    similarity = float(np.dot(reference_vector, candidate_vector) / (reference_norm * candidate_norm))
    similarity = max(min(similarity, 1.0), -1.0)
    return 1.0 - similarity


def verify_candidate_embedding(
    candidate_embedding: np.ndarray,
    reference_data: ReferenceData,
    threshold: float | None = None,
) -> VerificationResult:
    """Compare a candidate embedding against the stored reference."""

    active_threshold = float(threshold if threshold is not None else reference_data.threshold)
    distance = cosine_distance(reference_data.embedding, candidate_embedding)
    matched = distance <= active_threshold

    return VerificationResult(
        status="match" if matched else "unknown",
        matched=matched,
        access_granted=matched,
        label=reference_data.label,
        face_count=1,
        distance=distance,
        threshold=active_threshold,
        boxes=[],
        message="Welcome to the wishes page." if matched else "Girl not found.",
        next_screen=MATCH_SCREEN if matched else FAIL_SCREEN,
        should_redirect=matched,
    )


def verify_image_against_reference(
    image_path: str | Path,
    reference_data: ReferenceData,
    threshold: float | None = None,
    max_dimension: int = DEFAULT_MAX_INFERENCE_DIMENSION,
) -> VerificationResult:
    """Verify an image on disk against the enrolled reference."""

    image = load_image(image_path)
    return verify_frame_against_reference(
        image,
        reference_data,
        threshold=threshold,
        max_dimension=max_dimension,
    )


def verify_frame_against_reference(
    frame: np.ndarray,
    reference_data: ReferenceData,
    threshold: float | None = None,
    max_dimension: int = DEFAULT_MAX_INFERENCE_DIMENSION,
) -> VerificationResult:
    """Verify a live frame against the enrolled reference."""

    inference_frame, scale = resize_image_for_inference(frame, max_dimension=max_dimension)

    detections = detect_faces(inference_frame)
    inference_boxes = _extract_boxes(detections)
    boxes = _rescale_boxes(inference_boxes, scale)
    face_count = len(detections)

    if face_count == 0:
        return VerificationResult(
            status="no_face",
            matched=False,
            access_granted=False,
            label=reference_data.label,
            face_count=0,
            threshold=float(threshold if threshold is not None else reference_data.threshold),
            boxes=[],
            message="No face detected.",
            next_screen=CAMERA_SCREEN,
            should_redirect=False,
        )

    if face_count > 1:
        return VerificationResult(
            status="multiple_faces",
            matched=False,
            access_granted=False,
            label=reference_data.label,
            face_count=face_count,
            threshold=float(threshold if threshold is not None else reference_data.threshold),
            boxes=boxes,
            message="Only one face should be visible.",
            next_screen=CAMERA_SCREEN,
            should_redirect=False,
        )

    try:
        candidate_embedding = extract_embedding(
            image_source=inference_frame,
            model_name=reference_data.model_name,
            detector_backend=reference_data.detector_backend,
        )
    except FacePipelineError:
        try:
            candidate_embedding = extract_embedding_from_face_crop(
                image=inference_frame,
                face_box=inference_boxes[0],
                model_name=reference_data.model_name,
            )
        except FacePipelineError:
            return VerificationResult(
                status="no_face",
                matched=False,
                access_granted=False,
                label=reference_data.label,
                face_count=1,
                threshold=float(threshold if threshold is not None else reference_data.threshold),
                boxes=boxes,
                message="Face detected but not stable enough. Hold still and try again.",
                next_screen=CAMERA_SCREEN,
                should_redirect=False,
            )

    decision = verify_candidate_embedding(
        candidate_embedding=candidate_embedding,
        reference_data=reference_data,
        threshold=threshold,
    )
    decision.boxes = boxes
    return decision


def warm_up_models(model_name: str = MODEL_NAME) -> float:
    """Warm up the heavy recognition models so the first real request is faster."""

    started_at = time.perf_counter()

    try:
        if hasattr(DeepFace, "build_model"):
            DeepFace.build_model(model_name)
    except Exception:
        pass

    try:
        if hasattr(RetinaFace, "build_model"):
            RetinaFace.build_model()
    except Exception:
        pass

    return time.perf_counter() - started_at
