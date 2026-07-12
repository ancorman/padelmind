"""
Phase 2a (prototype) — ball trajectory from the custom model's ball detections.

NOT ByteTrack. A ball is one small, fast object that disappears for many frames
(recall ~0.46 on the current model, worse behind glass). ByteTrack is built to
keep MANY persistent objects apart — wrong tool. Instead: take the best ball box
per frame, run a constant-velocity Kalman filter, and interpolate short gaps.

Tier P / "Coming soon" per PHASE_FEATURE_MAP — prototype only, not a live surface
yet. Output feeds future: ball-speed, shot moments for smarter highlights,
serve detection.
"""

import numpy as np

BALL_CLASS = 0
MAX_GAP_FRAMES = 8        # interpolate across up to this many missing frames
GATE_DIST_PX = 250        # reject a detection this far from the prediction (outlier)


class _Kalman:
    """Constant-velocity 2D Kalman filter (state: x, y, vx, vy)."""

    def __init__(self, x, y, dt=0.2):
        self.dt = dt
        self.x = np.array([x, y, 0.0, 0.0], dtype=float)
        self.P = np.eye(4) * 100.0
        self.F = np.array([[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float)
        self.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=float)
        self.Q = np.eye(4) * 2.0
        self.R = np.eye(2) * 10.0

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x[:2].copy()

    def update(self, z):
        y = np.array(z) - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.P = (np.eye(4) - K @ self.H) @ self.P


def best_ball(detections_raw):
    """Pick the single highest-confidence ball box centre, or None."""
    balls = [d for d in detections_raw if d.get("class_id") == BALL_CLASS]
    if not balls:
        return None
    b = max(balls, key=lambda d: d["conf"])
    x1, y1, x2, y2 = b["bbox"]
    return ((x1 + x2) / 2, (y1 + y2) / 2, b["conf"])


def track(frame_detections, fps=5.0):
    """
    frame_detections: [(timestamp, [ {bbox, conf, class_id}, ... ]), ...]
    Returns [{t, x, y, source: 'detected'|'predicted', conf}] — ball path with
    short gaps filled. Long gaps (> MAX_GAP_FRAMES) break the track (ball out of play).
    """
    kf = None
    gap = 0
    path = []
    for t, dets in frame_detections:
        obs = best_ball(dets)

        if kf is None:
            if obs:
                kf = _Kalman(obs[0], obs[1], dt=1.0 / fps)
                path.append({"t": t, "x": obs[0], "y": obs[1], "source": "detected", "conf": obs[2]})
            continue

        pred = kf.predict()
        if obs and np.hypot(obs[0] - pred[0], obs[1] - pred[1]) <= GATE_DIST_PX:
            kf.update((obs[0], obs[1]))
            gap = 0
            path.append({"t": t, "x": float(kf.x[0]), "y": float(kf.x[1]),
                         "source": "detected", "conf": obs[2]})
        else:
            gap += 1
            if gap > MAX_GAP_FRAMES:
                kf = None                     # ball lost — end this segment
                continue
            path.append({"t": t, "x": float(pred[0]), "y": float(pred[1]),
                         "source": "predicted", "conf": 0.0})
    return path


def summary(path):
    det = [p for p in path if p["source"] == "detected"]
    return {
        "points": len(path),
        "detected": len(det),
        "interpolated": len(path) - len(det),
        "detection_rate_pct": round(100 * len(det) / max(len(path), 1), 1),
    }
