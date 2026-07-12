#!/usr/bin/env python3
"""
Phase 2b — generate coach labeling candidates at STRIKING moments.

Samples a match, runs YOLOv8-pose, scores each player pose for "is this a shot"
(arm raised overhead and/or extended = strike or wind-up), keeps the top moments,
and renders BIG, BOLD skeleton crops the coach can actually read.

Output:
  <out>/snap_XXX.jpg   — upscaled crop with a thick custom skeleton
  <out>/manifest.json  — [{id, source_frame_sec, strike_score, bbox, keypoints}]

Usage:
  .venv/bin/python pose_label_gen.py <video> <out_dir> [max_snaps]
"""

import json
import math
import os
import sys

import cv2
import numpy as np
from ultralytics import YOLO

import extract as ex

# COCO-17 skeleton, grouped so we can colour by body part (BGR)
LIMBS = [
    ((5, 7), (0, 220, 255)), ((7, 9), (0, 220, 255)),      # left arm  — amber
    ((6, 8), (0, 220, 255)), ((8, 10), (0, 220, 255)),     # right arm — amber
    ((11, 13), (120, 230, 120)), ((13, 15), (120, 230, 120)),  # left leg — green
    ((12, 14), (120, 230, 120)), ((14, 16), (120, 230, 120)),  # right leg — green
    ((5, 6), (240, 240, 240)), ((11, 12), (240, 240, 240)),    # shoulders / hips — white
    ((5, 11), (240, 240, 240)), ((6, 12), (240, 240, 240)),    # torso sides — white
]
KV = 0.3  # keypoint visibility threshold


def _device():
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _pt(kpts, j):
    x, y, c = kpts[j]
    return (x, y) if c > KV else None


def strike_score(kpts):
    """High when a wrist is raised above the shoulder and/or extended far from the
    body — i.e. the player is striking or winding up. 0 if we can't tell."""
    ls, rs = _pt(kpts, 5), _pt(kpts, 6)
    lh, rh = _pt(kpts, 11), _pt(kpts, 12)
    lw, rw = _pt(kpts, 9), _pt(kpts, 10)
    if not (ls and rs and lh and rh):
        return 0.0
    sh_mid = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)
    hip_mid = ((lh[0] + rh[0]) / 2, (lh[1] + rh[1]) / 2)
    torso = math.hypot(sh_mid[0] - hip_mid[0], sh_mid[1] - hip_mid[1]) or 1.0
    best = 0.0
    for sh, wr in ((ls, lw), (rs, rw)):
        if not wr:
            continue
        raised = (sh[1] - wr[1]) / torso           # + when wrist ABOVE shoulder (y down)
        extend = math.hypot(wr[0] - sh[0], wr[1] - sh[1]) / torso
        best = max(best, max(0.0, raised) * 1.6 + extend * 0.7)
    return best


def full_body(kpts, box):
    def seen(j):
        return kpts[j][2] > KV
    shoulders = seen(5) or seen(6)
    hips = seen(11) or seen(12)
    legs = seen(13) or seen(14) or seen(15) or seen(16)
    bh, bw = box[3] - box[1], box[2] - box[0]
    return shoulders and hips and legs and bh >= 70 and bh > bw


def draw_skeleton(img, kpts, ox, oy, scale):
    """Draw a bold, PROPORTIONATE skeleton. Sizes are a % of the final image
    height so joints stay small dots and limbs stay clean at any upscale factor."""
    H = img.shape[0]
    lw = max(2, int(H * 0.010))      # limb thickness  (~5px at 480)
    r = max(3, int(H * 0.012))       # joint radius    (~6px at 480)

    def P(j):
        x, y, c = kpts[j]
        if c <= KV:
            return None
        return (int((x - ox) * scale), int((y - oy) * scale))

    for (a, b), col in LIMBS:
        pa, pb = P(a), P(b)
        if pa and pb:
            cv2.line(img, pa, pb, (20, 20, 20), lw + 2)   # dark outline for contrast
            cv2.line(img, pa, pb, col, lw)
    for j in range(17):
        p = P(j)
        if p:
            cv2.circle(img, p, r + 1, (20, 20, 20), -1)
            cv2.circle(img, p, r, (80, 160, 255) if j in (9, 10) else (255, 255, 255), -1)  # wrists pop
    return img


def main():
    video = sys.argv[1]
    out_dir = sys.argv[2]
    max_snaps = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    os.makedirs(out_dir, exist_ok=True)

    model = YOLO("yolov8s-pose.pt")
    candidates = []  # (strike_score, ts, frame, kpts, box)

    for ts, frame in ex.frames(video, target_fps=6.0):
        r = model.predict(frame, device=_device(), conf=0.5, verbose=False)[0]
        if r.keypoints is None:
            continue
        xy = r.keypoints.xy.cpu().numpy()
        kc = r.keypoints.conf.cpu().numpy() if r.keypoints.conf is not None else None
        boxes = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else None
        if xy.ndim != 3 or xy.shape[0] == 0 or xy.shape[1] < 17 or boxes is None:
            continue
        for i in range(len(boxes)):
            kpts = [[float(xy[i][j][0]), float(xy[i][j][1]),
                     float(kc[i][j]) if kc is not None else 1.0] for j in range(17)]
            if not full_body(kpts, boxes[i]):
                continue
            sc = strike_score(kpts)
            if sc > 0.15:  # some arm action
                candidates.append((sc, ts, frame.copy(), kpts, boxes[i]))

    # Top strike moments, but spread across time (>=1s apart) so we don't get dupes
    candidates.sort(key=lambda c: c[0], reverse=True)
    chosen, used_ts = [], []
    for c in candidates:
        if len(chosen) >= max_snaps:
            break
        if all(abs(c[1] - t) >= 1.0 for t in used_ts):
            chosen.append(c)
            used_ts.append(c[1])
    chosen.sort(key=lambda c: c[1])  # chronological

    manifest = []
    for idx, (sc, ts, frame, kpts, box) in enumerate(chosen):
        x1, y1, x2, y2 = box
        padx = (x2 - x1) * 0.35
        pady = (y2 - y1) * 0.20
        h, w = frame.shape[:2]
        cx1, cy1 = max(0, int(x1 - padx)), max(0, int(y1 - pady))
        cx2, cy2 = min(w, int(x2 + padx)), min(h, int(y2 + pady))
        crop = frame[cy1:cy2, cx1:cx2]
        if crop.size == 0:
            continue
        # Upscale to a readable size, then a light denoise so it's less pixelated
        target_h = 480
        scale = max(1.0, target_h / crop.shape[0])
        crop = cv2.resize(crop, (int(crop.shape[1] * scale), int(crop.shape[0] * scale)),
                          interpolation=cv2.INTER_CUBIC)
        crop = cv2.bilateralFilter(crop, 7, 60, 60)   # smooth upscale blockiness
        draw_skeleton(crop, kpts, cx1, cy1, scale)

        fn = f"snap_{idx:03d}.jpg"
        cv2.imwrite(os.path.join(out_dir, fn), crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
        manifest.append({
            "id": fn,
            "source_frame_sec": round(ts, 2),
            "strike_score": round(sc, 2),
            "bbox": [round(float(v), 1) for v in (x1, y1, x2, y2)],
            "keypoints": [[round(k[0], 1), round(k[1], 1), round(k[2], 3)] for k in kpts],
        })

    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {len(manifest)} strike-moment snapshots to {out_dir}")


if __name__ == "__main__":
    main()
