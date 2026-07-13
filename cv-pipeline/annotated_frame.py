#!/usr/bin/env python3
"""
Full-frame match annotation, Padel-AI style — court lines + thin skeletons +
racket boxes, all overlaid on the live frame. Combines the three pieces we
already have: auto-calibration (net + serve lines -> court), YOLOv8-pose, and
the custom model's racket detections.

Skeleton is deliberately THIN so it reads as data over the game, not a cartoon.

Usage:  YOLO_MODEL=models/padel_yolov8s_wpt_v11.pt \
          python annotated_frame.py <frame.jpg> <out.jpg>
"""

import sys
import cv2
import numpy as np
from ultralytics import YOLO
from auto_calibrate import auto_homography

# BGR
COURT_OUTER = (255, 120, 40)     # blue — outline + net
COURT_INNER = (200, 60, 220)     # magenta/pink — service + centre lines
RACKET = (60, 220, 255)          # yellow
KV = 0.35

# COCO-17 skeleton, thin, coloured by part (BGR)
LIMBS = [
    ((5, 7), (90, 220, 90)), ((7, 9), (90, 220, 90)),        # left arm  green
    ((6, 8), (90, 220, 90)), ((8, 10), (90, 220, 90)),       # right arm green
    ((11, 13), (210, 90, 220)), ((13, 15), (210, 90, 220)),  # left leg  magenta
    ((12, 14), (210, 90, 220)), ((14, 16), (210, 90, 220)),  # right leg magenta
    ((5, 6), (240, 240, 240)), ((11, 12), (240, 240, 240)),  # shoulders/hips
    ((5, 11), (240, 240, 240)), ((6, 12), (240, 240, 240)),
]


def draw_court(vis, H):
    Hinv = np.linalg.inv(H)
    def w2i(x, y):
        p = cv2.perspectiveTransform(np.float32([[[x, y]]]), Hinv)[0][0]
        return int(round(p[0])), int(round(p[1]))
    outer = [((0, 0), (10, 0)), ((0, 20), (10, 20)), ((0, 0), (0, 20)),
             ((10, 0), (10, 20)), ((0, 10), (10, 10))]
    inner = [((0, 3), (10, 3)), ((0, 17), (10, 17)), ((5, 3), (5, 17))]
    for a, b in outer:
        cv2.line(vis, w2i(*a), w2i(*b), COURT_OUTER, 2, cv2.LINE_AA)
    for a, b in inner:
        cv2.line(vis, w2i(*a), w2i(*b), COURT_INNER, 2, cv2.LINE_AA)


def draw_skeletons(vis, img):
    H, W = img.shape[:2]
    lw = max(2, int(H * 0.004))          # THIN — ~2px on 480, doesn't overpower
    r = max(2, int(H * 0.006))
    ps = YOLO("yolov8s-pose.pt").predict(img, conf=0.4, verbose=False)[0]
    if ps.keypoints is None:
        return
    xy = ps.keypoints.xy.cpu().numpy()
    cf = ps.keypoints.conf.cpu().numpy() if ps.keypoints.conf is not None else None
    if xy.ndim != 3 or xy.shape[1] < 17:
        return
    for i in range(len(xy)):
        def P(j):
            if cf is not None and cf[i][j] <= KV:
                return None
            return (int(xy[i][j][0]), int(xy[i][j][1]))
        drawn = set()
        for (a, b), col in LIMBS:
            pa, pb = P(a), P(b)
            if pa and pb:
                cv2.line(vis, pa, pb, col, lw, cv2.LINE_AA)
                drawn.update((a, b))
        for j in drawn:
            p = P(j)
            if p:
                cv2.circle(vis, p, r, (255, 255, 255), -1, cv2.LINE_AA)


def draw_rackets(vis, img):
    m = YOLO("models/padel_yolov8s_wpt_v11.pt").predict(img, conf=0.3, verbose=False)[0]
    for b in m.boxes:
        if int(b.cls[0]) == 3:            # racket class
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            cv2.rectangle(vis, (x1, y1), (x2, y2), RACKET, 2, cv2.LINE_AA)


def main():
    frame_path, out_path = sys.argv[1], sys.argv[2]
    img = cv2.imread(frame_path)
    vis = img.copy()
    H, msg = auto_homography(img)
    if H is not None:
        draw_court(vis, H)
    else:
        print("court auto-cal skipped:", msg)
    draw_skeletons(vis, img)
    draw_rackets(vis, img)
    cv2.imwrite(out_path, vis)
    print(f"annotated frame -> {out_path}")


if __name__ == "__main__":
    main()
