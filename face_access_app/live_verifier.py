"""Live webcam verification against the enrolled reference face."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

try:
    from .face_pipeline import verify_frame_against_reference
    from .storage import get_default_reference_path, load_reference
except ImportError:  # pragma: no cover - supports direct script execution
    from face_pipeline import verify_frame_against_reference
    from storage import get_default_reference_path, load_reference


STATUS_COLORS = {
    "match": (0, 180, 0),
    "unknown": (0, 0, 220),
    "no_face": (0, 200, 255),
    "multiple_faces": (0, 140, 255),
}


def _draw_boxes(frame, boxes, color):
    for x1, y1, x2, y2 in boxes:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)


def _build_status_text(result, stable_match: bool, match_streak: int, required_streak: int) -> str:
    if result.status == "match":
        status_label = "TRUE" if stable_match else "MATCHING"
        return (
            f"{status_label}: {result.label} "
            f"({result.distance:.4f} <= {result.threshold:.4f}) "
            f"[{match_streak}/{required_streak}]"
        )

    if result.status == "unknown":
        return (
            f"FALSE: unknown "
            f"({result.distance:.4f} > {result.threshold:.4f})"
        )

    if result.status == "multiple_faces":
        return "MULTIPLE FACES"

    return "NO FACE"


def run_live_verification(
    reference_path: str | Path | None = None,
    camera_index: int = 0,
    threshold: float | None = None,
    required_consecutive_matches: int = 3,
    exit_on_match: bool = False,
) -> bool:
    """Run the live camera loop and return whether a stable match was seen."""

    reference_data = load_reference(reference_path)
    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        raise RuntimeError(f"Failed to open camera index {camera_index}.")

    match_streak = 0
    saw_stable_match = False

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("Failed to read a frame from the camera.")

            result = verify_frame_against_reference(
                frame=frame,
                reference_data=reference_data,
                threshold=threshold,
            )

            if result.matched:
                match_streak += 1
            else:
                match_streak = 0

            stable_match = result.matched and match_streak >= required_consecutive_matches
            saw_stable_match = saw_stable_match or stable_match

            color = STATUS_COLORS.get(result.status, (255, 255, 255))
            _draw_boxes(frame, result.boxes or [], color)

            overlay_text = _build_status_text(
                result=result,
                stable_match=stable_match,
                match_streak=match_streak,
                required_streak=required_consecutive_matches,
            )
            cv2.putText(
                frame,
                overlay_text,
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
                cv2.LINE_AA,
            )

            cv2.imshow("Face Access", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if exit_on_match and stable_match:
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()

    return saw_stable_match


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run live webcam verification.")
    parser.add_argument(
        "--reference",
        type=Path,
        default=get_default_reference_path(),
        help="Path to the saved .npz reference file.",
    )
    parser.add_argument("--camera-index", type=int, default=0, help="Webcam device index.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Override the stored threshold during live verification.",
    )
    parser.add_argument(
        "--required-consecutive-matches",
        type=int,
        default=3,
        help="Frames required before a match is treated as stable true.",
    )
    parser.add_argument(
        "--exit-on-match",
        action="store_true",
        help="Exit automatically once a stable match is detected.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    matched = run_live_verification(
        reference_path=args.reference,
        camera_index=args.camera_index,
        threshold=args.threshold,
        required_consecutive_matches=max(1, args.required_consecutive_matches),
        exit_on_match=args.exit_on_match,
    )
    print({"matched": matched})
    return 0 if matched else 1


if __name__ == "__main__":
    raise SystemExit(main())

