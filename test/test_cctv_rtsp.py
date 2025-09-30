import os
import time
from typing import Optional, Tuple

import pytest


try:
    import cv2  # type: ignore
except Exception as import_error:  # pragma: no cover
    cv2 = None  # Allow tests to be skipped gracefully if OpenCV isn't installed
    _cv2_import_error = import_error
else:
    _cv2_import_error = None


RTSP_ENV_VAR = "rtsp://admin:endank122@192.168.1.64:554/Streaming/Channels/101"
DEFAULT_OPEN_TIMEOUT_SECONDS = float(os.getenv("RTSP_OPEN_TIMEOUT_SECONDS", "10"))
DEFAULT_READ_TIMEOUT_SECONDS = float(os.getenv("RTSP_READ_TIMEOUT_SECONDS", "10"))
FRAME_READ_ATTEMPTS = int(os.getenv("RTSP_FRAME_READ_ATTEMPTS", "20"))
FPS_SAMPLE_FRAMES = int(os.getenv("RTSP_FPS_SAMPLE_FRAMES", "30"))


def _require_opencv() -> None:
    if cv2 is None:
        pytest.skip(f"opencv-python not available: {_cv2_import_error}")


def _get_rtsp_url() -> str:
    # Allow using a literal RTSP URL in the env var name slot for convenience
    if RTSP_ENV_VAR.lower().startswith("rtsp://"):
        return RTSP_ENV_VAR

    rtsp_url = os.getenv(RTSP_ENV_VAR, "").strip()
    if not rtsp_url:
        pytest.skip(
            f"Missing {RTSP_ENV_VAR}. Set it to your camera RTSP URL to run this test."
        )
    return rtsp_url


def _open_capture(rtsp_url: str, open_timeout_seconds: float) -> "cv2.VideoCapture":
    # Use FFMPEG backend if available for better RTSP handling
    # Note: The flag may be ignored depending on the build
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

    if cap.isOpened():
        return cap

    # Retry opening within timeout window (some cameras need a bit of time)
    deadline = time.time() + open_timeout_seconds
    while time.time() < deadline:
        cap.release()
        time.sleep(0.5)
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            break

    return cap


def _read_first_frame(
    cap: "cv2.VideoCapture", read_timeout_seconds: float, attempts: int
) -> Tuple[bool, Optional["cv2.Mat"]]:
    deadline = time.time() + read_timeout_seconds
    last_frame = None
    for _ in range(max(1, attempts)):
        if time.time() > deadline:
            break
        ok, frame = cap.read()
        if ok and frame is not None:
            return True, frame
        last_frame = frame
        time.sleep(0.1)
    return False, last_frame


@pytest.mark.integration
def test_rtsp_can_connect_and_read_frame():
    _require_opencv()
    rtsp_url = _get_rtsp_url()

    cap = _open_capture(rtsp_url, DEFAULT_OPEN_TIMEOUT_SECONDS)
    try:
        assert cap.isOpened(), (
            "Failed to open RTSP stream. Ensure the URL is reachable and credentials are correct."
        )

        ok, frame = _read_first_frame(
            cap, DEFAULT_READ_TIMEOUT_SECONDS, FRAME_READ_ATTEMPTS
        )
        assert ok, (
            "Opened RTSP but couldn't read a frame within the timeout. "
            "Check network stability, camera availability, and stream codecs."
        )

        # Basic sanity on frame dimensions
        height, width = frame.shape[:2]  # type: ignore[attr-defined]
        assert width > 0 and height > 0, "Received an empty frame (zero dimensions)."
    finally:
        cap.release()


@pytest.mark.integration
def test_rtsp_estimated_fps_is_reasonable():
    _require_opencv()
    rtsp_url = _get_rtsp_url()

    cap = _open_capture(rtsp_url, DEFAULT_OPEN_TIMEOUT_SECONDS)
    try:
        assert cap.isOpened(), "Failed to open RTSP stream."

        # Warm-up read
        _read_first_frame(cap, DEFAULT_READ_TIMEOUT_SECONDS, FRAME_READ_ATTEMPTS)

        target_frames = max(5, FPS_SAMPLE_FRAMES)
        collected = 0
        start_time = time.time()
        deadline = start_time + DEFAULT_READ_TIMEOUT_SECONDS + 10
        while collected < target_frames and time.time() < deadline:
            ok, frame = cap.read()
            if ok and frame is not None:
                collected += 1
        elapsed = time.time() - start_time

        # Avoid division by zero
        if elapsed <= 0:
            pytest.skip("Elapsed time too small to compute FPS; retry locally.")

        fps = collected / elapsed

        # We don't strictly fail on low FPS because networks vary; just assert it's not zero
        assert fps > 0.1, f"Measured FPS seems too low: {fps:.2f}"
    finally:
        cap.release()

if __name__ == "__main__":
    # Allow running directly: `python test_cctv_rtsp.py`
    # Equivalent to invoking via pytest
    import pytest as _pytest  # local import to avoid polluting globals
    raise SystemExit(_pytest.main([__file__]))

