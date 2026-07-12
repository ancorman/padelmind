import numpy as np
import cv2

# Standard padel court world coordinates (metres).
# Matches the 12-point order used in the calibration tool.
WORLD_PTS = np.float32([
    [0,   0 ],   # 1  near-left corner
    [10,  0 ],   # 2  near-right corner
    [0,   3 ],   # 3  near service line — left
    [10,  3 ],   # 4  near service line — right
    [5,   3 ],   # 5  center T (near)
    [0,   10],   # 6  net — left wall
    [10,  10],   # 7  net — right wall
    [0,   17],   # 8  far service line — left
    [10,  17],   # 9  far service line — right
    [5,   17],   # 10 center T (far)
    [0,   20],   # 11 far-left corner
    [10,  20],   # 12 far-right corner
])


class CourtHomography:
    def __init__(self, keypoints_data: dict | None):
        """
        keypoints_data is the dict stored in padel_courts.camera_keypoints:
        {
          "image_width": int, "image_height": int,
          "points": [{"n": 1, "label": "...", "x": px, "y": py}, ...]
        }
        If None/empty, project() returns None (no calibration yet).
        """
        self._H = None
        if keypoints_data and keypoints_data.get("points"):
            # Map each provided point to its world coord BY NUMBER, so a subset
            # (e.g. near corners off-frame) still calibrates. Needs >= 4 points.
            pts = [p for p in keypoints_data["points"] if 1 <= p.get("n", 0) <= 12]
            if len(pts) >= 4:
                cam_pts = np.float32([[p["x"], p["y"]] for p in pts])
                world_pts = np.float32([WORLD_PTS[p["n"] - 1] for p in pts])
                self._H, _ = cv2.findHomography(cam_pts, world_pts, cv2.RANSAC, 5.0)

    def project(self, px: float, py: float) -> tuple[float, float] | None:
        """Project a camera pixel coordinate to court metres. Returns None if uncalibrated."""
        if self._H is None:
            return None
        pt = np.float32([[[px, py]]])
        result = cv2.perspectiveTransform(pt, self._H)
        x, y = float(result[0][0][0]), float(result[0][0][1])
        # Clamp to court bounds
        x = max(0.0, min(10.0, x))
        y = max(0.0, min(20.0, y))
        return x, y

    @property
    def calibrated(self) -> bool:
        return self._H is not None
