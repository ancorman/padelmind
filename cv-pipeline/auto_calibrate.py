#!/usr/bin/env python3
"""
Auto-calibration prototype — no manual 12-point clicking.

A padel court is a fixed 10m x 20m template. The custom model detects the NET
and the two SERVE LINES as objects; those three horizontals (with their known
world y = 10 / 3 / 17 and court width 0..10) give 6 reference points, enough to
solve the homography automatically.

Validation: reproject the standard court onto the frame using the auto-derived
homography. If the drawn court lines land on the real court lines, it worked.

Usage:  YOLO_MODEL=models/padel_yolov8s_wpt_v11.pt \
          python auto_calibrate.py <frame.jpg> <out.jpg>
"""

import sys
import cv2
import os
import numpy as np
from ultralytics import YOLO

NET_CLS, SERVE_CLS = 1, 4


def auto_homography(img):
    m = YOLO(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "models", "padel_yolov8s_wpt_v11.pt"))
    # conf 0.1: serve lines are thin/low-contrast and often score ~0.15; RANSAC
    # below tolerates the extra noise the lower threshold lets in.
    r = m.predict(img, conf=0.10, verbose=False)[0]
    nets, serves = [], []
    for b in r.boxes:
        c = int(b.cls[0])
        box = b.xyxy[0].tolist()
        if c == NET_CLS:
            nets.append(box)
        elif c == SERVE_CLS:
            serves.append(box)

    # dedupe serve lines that overlap vertically (same line detected twice)
    serves.sort(key=lambda b: (b[1] + b[3]) / 2)
    dedup = []
    for s in serves:
        yc = (s[1] + s[3]) / 2
        if dedup and abs(yc - (dedup[-1][1] + dedup[-1][3]) / 2) < img.shape[0] * 0.04:
            if (s[2] - s[0]) > (dedup[-1][2] - dedup[-1][0]):
                dedup[-1] = s                              # keep the wider box
            continue
        dedup.append(s)
    serves = dedup

    if len(serves) < 2:
        return None, f"need 2 serve lines (got net={len(nets)}, serve={len(serves)})"

    far, near = serves[0], serves[-1]                     # higher in image = far

    def edges(b, wy):
        yc = (b[1] + b[3]) / 2
        return [([b[0], yc], [0, wy]), ([b[2], yc], [10, wy])]

    pairs = edges(far, 17) + edges(near, 3)
    if nets:                                              # net adds 2 more points when seen
        net = max(nets, key=lambda b: b[2] - b[0])
        pairs += edges(net, 10)
    img_pts = np.float32([p[0] for p in pairs])
    world_pts = np.float32([p[1] for p in pairs])
    H, _ = cv2.findHomography(img_pts, world_pts, cv2.RANSAC, 5.0)   # image -> world
    if H is None:
        return None, "findHomography failed"
    return H, f"ok ({len(pairs)} pts, net={'yes' if nets else 'no'})"


def main():
    frame_path, out_path = sys.argv[1], sys.argv[2]
    img = cv2.imread(frame_path)
    H, msg = auto_homography(img)
    if H is None:
        print("auto-calibration failed:", msg)
        return
    Hinv = np.linalg.inv(H)                                # world -> image

    def w2i(x, y):
        p = cv2.perspectiveTransform(np.float32([[[x, y]]]), Hinv)[0][0]
        return int(round(p[0])), int(round(p[1]))

    court = [
        ((0, 0), (10, 0)), ((0, 20), (10, 20)),           # baselines
        ((0, 0), (0, 20)), ((10, 0), (10, 20)),           # side walls
        ((0, 10), (10, 10)),                              # net
        ((0, 3), (10, 3)), ((0, 17), (10, 17)),           # service lines
        ((5, 3), (5, 17)),                                # centre line
    ]
    vis = img.copy()
    for a, b in court:
        cv2.line(vis, w2i(*a), w2i(*b), (0, 255, 0), 2)
    cv2.imwrite(out_path, vis)
    print(f"auto-calibrated from net + 2 serve lines. Reprojected court -> {out_path}")


if __name__ == "__main__":
    main()
