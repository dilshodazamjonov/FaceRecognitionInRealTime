"""Simple one-file entry point for reading a saved reference .npz file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
PYTHON_ROOT = REPO_ROOT / "python"

if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from face_access_app.storage import (  # noqa: E402
    DEFAULT_REFERENCE_DIR,
    get_default_reference_path,
    load_reference,
)


def find_first_reference(reference_dir: Path = DEFAULT_REFERENCE_DIR) -> Path:
    reference_paths = sorted(reference_dir.glob("*.npz"))
    if not reference_paths:
        raise FileNotFoundError(f"No reference files found in: {reference_dir}")
    return reference_paths[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read one saved reference .npz file and display its contents."
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=None,
        help=(
            "Path to the saved reference .npz file. "
            "Defaults to the main reference file if it exists, otherwise the first .npz in references/."
        ),
    )
    return parser


def resolve_reference_path(input_path: Path | None) -> Path:
    if input_path is not None:
        return input_path

    default_path = get_default_reference_path()
    if default_path.exists():
        return default_path

    return find_first_reference()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    reference_path = resolve_reference_path(args.reference)
    reference = load_reference(reference_path)
    preview = [round(float(value), 6) for value in reference.embedding[:8]]

    payload = {
        "reference_path": str(reference_path),
        "label": reference.label,
        "source_image_path": reference.source_image_path,
        "threshold": reference.threshold,
        "model_name": reference.model_name,
        "detector_backend": reference.detector_backend,
        "embedding_size": int(reference.embedding.size),
        "embedding_preview": preview,
    }
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
