"""Enrollment script for creating a single saved reference embedding."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    from .face_pipeline import (
        DEFAULT_MATCH_THRESHOLD,
        DETECTOR_BACKEND,
        MODEL_NAME,
        extract_single_face_embedding,
        find_first_image,
    )
    from .storage import get_default_reference_path, save_reference_variants
except ImportError:  # pragma: no cover - supports direct script execution
    from face_pipeline import (
        DEFAULT_MATCH_THRESHOLD,
        DETECTOR_BACKEND,
        MODEL_NAME,
        extract_single_face_embedding,
        find_first_image,
    )
    from storage import get_default_reference_path, save_reference_variants


def enroll_reference(
    image_path: str | Path,
    label: str = "girlfriend",
    output_path: str | Path | None = None,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> Path:
    """Create and save the reference embedding for the enrolled identity."""

    return enroll_reference_from_image_source(
        image_source=image_path,
        source_image_path=image_path,
        label=label,
        output_path=output_path,
        threshold=threshold,
    )


def enroll_reference_from_image_source(
    image_source: str | Path | Any,
    source_image_path: str | Path,
    label: str = "girlfriend",
    output_path: str | Path | None = None,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
    archive_output_path: str | Path | None = None,
) -> Path:
    """Create and save the reference embedding from a path or in-memory image."""

    embedding_result = extract_single_face_embedding(
        image_source=image_source,
        model_name=MODEL_NAME,
        detector_backend=DETECTOR_BACKEND,
    )
    primary_path = Path(output_path) if output_path else get_default_reference_path()
    output_paths = [primary_path]
    if archive_output_path is not None:
        output_paths.append(Path(archive_output_path))

    saved_paths = save_reference_variants(
        embedding=embedding_result.embedding,
        label=label,
        output_paths=output_paths,
        source_image_path=source_image_path,
        threshold=threshold,
        model_name=MODEL_NAME,
        detector_backend=DETECTOR_BACKEND,
    )
    return saved_paths[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Enroll one reference face from an image.")
    parser.add_argument(
        "--image",
        type=Path,
        default=None,
        help="Path to the reference image. Defaults to the first image in the repo data/ folder.",
    )
    parser.add_argument(
        "--label",
        default="girlfriend",
        help="Label stored with the enrolled reference.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=get_default_reference_path(),
        help="Path to the output .npz reference file.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_MATCH_THRESHOLD,
        help="Cosine distance threshold used for later verification.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    image_path = args.image if args.image is not None else find_first_image()
    saved_path = enroll_reference(
        image_path=image_path,
        label=args.label,
        output_path=args.out,
        threshold=args.threshold,
    )
    print(f"Saved reference for '{args.label}' to: {saved_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
