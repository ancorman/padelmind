import os
import torch
import numpy as np
from ultralytics import YOLO

# Auto-detect best available device
def _device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


_model: YOLO | None = None

def _get_model() -> YOLO:
    global _model
    if _model is None:
        # Use Roboflow padel model if env var set, else fall back to YOLOv8n
        model_path = os.environ.get("YOLO_MODEL", "yolov8n.pt")
        _model = YOLO(model_path)
    return _model


def detect_players(frame: np.ndarray, conf: float = 0.4) -> list[dict]:
    """
    Returns list of {bbox: [x1,y1,x2,y2], conf: float, foot: [x,y]}
    foot is the midpoint of the bottom edge (proxy for player's court position).
    """
    model = _get_model()
    results = model.predict(
        frame,
        device=_device(),
        classes=[0],        # person only
        conf=conf,
        verbose=False,
    )

    detections = []
    for box in results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        detections.append({
            "bbox": [x1, y1, x2, y2],
            "conf": float(box.conf[0]),
            "foot": [(x1 + x2) / 2, y2],   # foot = bottom-centre of bbox
        })
    return detections
