"""
Phase 2b (prototype) — player pose via off-the-shelf YOLOv8-pose (COCO-pretrained).

Needs NO Roboflow data — pose ships pretrained on 17-keypoint COCO skeletons.
The custom detector's player boxes are still useful downstream to attach each
skeleton to a tracked slot (1-4); this module just extracts the raw skeletons.

Spike result (WPT 720p clip, M2/MPS): 100% frame coverage, ~28 FPS, 17 kpts/player.

Tier P / "Coming soon" per PHASE_FEATURE_MAP — prototype only. Feeds future
coach-defined shot/technique intelligence (the coach MCQ workflow).
"""

import numpy as np

# COCO-17 keypoint order (what YOLOv8-pose emits)
KPT_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]

_model = None


def _get_model():
    global _model
    if _model is None:
        from ultralytics import YOLO
        _model = YOLO("yolov8s-pose.pt")
    return _model


def _device():
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def estimate(frame, conf=0.4):
    """
    Returns a list of skeletons, one per detected person:
      {bbox, conf, keypoints: [(x, y, visibility), x17], arm_extension}
    arm_extension = wrist-to-shoulder distance on the dominant side, normalised by
    torso length — a cheap proxy for "reaching/swinging" that a coach rule can build on.
    """
    m = _get_model()
    r = m.predict(frame, device=_device(), conf=conf, verbose=False)[0]
    if r.keypoints is None:
        return []

    xy = r.keypoints.xy.cpu().numpy()             # (n, 17, 2)
    # Guard every degenerate shape: no people (n=0) OR no keypoints axis (17→0)
    if xy.ndim != 3 or xy.shape[0] == 0 or xy.shape[1] < 17:
        return []

    out = []
    cf = r.keypoints.conf.cpu().numpy() if r.keypoints.conf is not None else None
    boxes = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else None
    bconf = r.boxes.conf.cpu().numpy() if r.boxes is not None else None

    for i in range(len(xy)):
        kpts = [(float(xy[i][j][0]), float(xy[i][j][1]),
                 float(cf[i][j]) if cf is not None else 1.0) for j in range(17)]
        out.append({
            "bbox": boxes[i].tolist() if boxes is not None else None,
            "conf": float(bconf[i]) if bconf is not None else 1.0,
            "keypoints": kpts,
            "arm_extension": _arm_extension(kpts),
        })
    return out


def _arm_extension(kpts):
    """Max normalised wrist-shoulder reach (proxy for a swing). None if joints unseen."""
    def pt(i):
        x, y, v = kpts[i]
        return np.array([x, y]) if v > 0.3 else None

    ls, rs = pt(5), pt(6)
    lw, rw = pt(9), pt(10)
    lh, rh = pt(11), pt(12)
    if ls is None or rs is None or lh is None or rh is None:
        return None
    torso = (np.linalg.norm((ls + rs) / 2 - (lh + rh) / 2)) or 1.0
    reaches = []
    if lw is not None:
        reaches.append(np.linalg.norm(lw - ls) / torso)
    if rw is not None:
        reaches.append(np.linalg.norm(rw - rs) / torso)
    return round(max(reaches), 2) if reaches else None
