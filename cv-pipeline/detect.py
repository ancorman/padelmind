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
_player_classes: list[int] = []

def _get_model() -> YOLO:
    global _model, _player_classes
    if _model is None:
        # Custom padel model via env var (e.g. /app/models/padel_yolov8s_wpt_v11.pt,
        # classes: ball/net/player/racket/serve line), else stock YOLOv8n (COCO).
        model_path = os.environ.get("YOLO_MODEL", "yolov8n.pt")
        _model = YOLO(model_path)
        # Class ids differ per model — resolve "the humans" by name, never hardcode.
        _player_classes = [i for i, n in _model.names.items() if n in ("person", "player")]
        if not _player_classes:
            raise ValueError(f"No person/player class in {model_path}: {_model.names}")
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
        classes=_player_classes,
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


def detect_all(frame: np.ndarray, conf: float = 0.25) -> list[dict]:
    """
    All classes the model knows (ball, net, player, racket, serve line for the
    custom model). Returns {bbox, conf, class_id}. Used by ball_track / pose crops.
    Lower default conf — the ball is faint and worth catching at lower confidence.
    """
    model = _get_model()
    results = model.predict(frame, device=_device(), conf=conf, verbose=False)
    out = []
    for box in results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        out.append({
            "bbox": [x1, y1, x2, y2],
            "conf": float(box.conf[0]),
            "class_id": int(box.cls[0]),
        })
    return out
