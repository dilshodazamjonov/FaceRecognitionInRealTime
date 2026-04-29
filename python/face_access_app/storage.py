"""Persistence helpers for a single enrolled reference face."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


DEFAULT_REFERENCE_DIR = Path(__file__).resolve().parent / "references"
DEFAULT_REFERENCE_PATH = DEFAULT_REFERENCE_DIR / "girlfriend_reference.npz"


class StorageError(RuntimeError):
    """Raised when a saved reference cannot be written or read."""


@dataclass(slots=True)
class ReferenceData:
    """Stored reference embedding plus the metadata needed to verify it."""

    label: str
    embedding: np.ndarray
    source_image_path: str
    threshold: float
    model_name: str
    detector_backend: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "source_image_path": self.source_image_path,
            "threshold": self.threshold,
            "model_name": self.model_name,
            "detector_backend": self.detector_backend,
            "embedding_size": int(self.embedding.size),
        }


def get_default_reference_path() -> Path:
    """Return the default location for the enrolled reference file."""

    return DEFAULT_REFERENCE_PATH


def save_reference(
    embedding: np.ndarray,
    label: str,
    output_path: str | Path | None,
    source_image_path: str | Path,
    threshold: float,
    model_name: str,
    detector_backend: str,
) -> Path:
    """Save the enrolled reference embedding and metadata to a .npz file."""

    target_path = Path(output_path) if output_path else DEFAULT_REFERENCE_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    normalized_embedding = np.asarray(embedding, dtype=np.float32).reshape(-1)
    if normalized_embedding.size == 0:
        raise StorageError("Embedding is empty and cannot be saved.")

    np.savez_compressed(
        target_path,
        embedding=normalized_embedding,
        label=str(label),
        source_image_path=str(source_image_path),
        threshold=float(threshold),
        model_name=str(model_name),
        detector_backend=str(detector_backend),
    )

    return target_path


def load_reference(input_path: str | Path | None = None) -> ReferenceData:
    """Load the saved reference embedding and metadata from a .npz file."""

    reference_path = Path(input_path) if input_path else DEFAULT_REFERENCE_PATH
    if not reference_path.exists():
        raise StorageError(f"Reference file does not exist: {reference_path}")

    try:
        with np.load(reference_path, allow_pickle=False) as payload:
            required_keys = {
                "embedding",
                "label",
                "source_image_path",
                "threshold",
                "model_name",
                "detector_backend",
            }
            missing_keys = required_keys.difference(payload.files)
            if missing_keys:
                missing_list = ", ".join(sorted(missing_keys))
                raise StorageError(
                    f"Reference file is missing required fields: {missing_list}"
                )

            embedding = np.asarray(payload["embedding"], dtype=np.float32).reshape(-1)
            if embedding.size == 0:
                raise StorageError("Reference embedding is empty.")

            return ReferenceData(
                label=str(payload["label"].item()),
                embedding=embedding,
                source_image_path=str(payload["source_image_path"].item()),
                threshold=float(payload["threshold"].item()),
                model_name=str(payload["model_name"].item()),
                detector_backend=str(payload["detector_backend"].item()),
            )
    except StorageError:
        raise
    except Exception as exc:  # pragma: no cover - defensive corruption handling
        raise StorageError(f"Failed to load reference file: {reference_path}") from exc

