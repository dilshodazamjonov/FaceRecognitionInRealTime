"""Image verification helpers for the single-reference face access flow."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .face_pipeline import DEFAULT_MATCH_THRESHOLD, verify_image_against_reference
    from .storage import get_default_reference_path, load_reference
except ImportError:  # pragma: no cover - supports direct script execution
    from face_pipeline import DEFAULT_MATCH_THRESHOLD, verify_image_against_reference
    from storage import get_default_reference_path, load_reference


def verify_image(
    image_path: str | Path,
    reference_path: str | Path | None = None,
    threshold: float | None = None,
):
    """Verify a candidate image against the saved reference."""

    reference_data = load_reference(reference_path)
    return verify_image_against_reference(
        image_path=image_path,
        reference_data=reference_data,
        threshold=threshold,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify one image against the saved reference.")
    parser.add_argument("--image", type=Path, required=True, help="Candidate image path.")
    parser.add_argument(
        "--reference",
        type=Path,
        default=get_default_reference_path(),
        help="Path to the saved .npz reference file.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help=f"Override the stored threshold. Default stored threshold is {DEFAULT_MATCH_THRESHOLD}.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    result = verify_image(
        image_path=args.image,
        reference_path=args.reference,
        threshold=args.threshold,
    )
    print(result.to_dict())
    return 0 if result.matched else 1


if __name__ == "__main__":
    raise SystemExit(main())

