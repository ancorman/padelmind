from typing import Generator
import cv2
import numpy as np


def frames(video_path: str, target_fps: float = 5.0) -> Generator[tuple[float, np.ndarray], None, None]:
    """Yield (timestamp_sec, frame) at target_fps, subsampling from source FPS."""
    cap = cv2.VideoCapture(video_path)
    source_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, round(source_fps / target_fps))
    frame_idx = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % step == 0:
                timestamp = frame_idx / source_fps
                yield timestamp, frame
            frame_idx += 1
    finally:
        cap.release()


def total_duration(video_path: str) -> float:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return count / fps
