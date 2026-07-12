#!/usr/bin/env python3
"""
Phase 2b — generate coach labeling candidates.

Samples frames from a match video, runs YOLOv8-pose, crops each detected player
with their skeleton drawn, and writes:
  <out>/snap_XXX.jpg      — skeleton-overlaid player crop (what the coach sees)
  <out>/manifest.json     — [{id, source_frame_sec, bbox, keypoints[17][x,y,conf]}]

The coach reviews the crops in coach_pose_review.html and answers MCQs; those
answers + these keypoints become the training set for the shot/technique model.

Usage:
  .venv/bin/python pose_label_gen.py <video> <out_dir> [max_snaps]
"""

import json
import os
import sys

import cv2
from ultralytics import YOLO

import extract as ex


def _device():
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main():
    video = sys.argv[1]
    out_dir = sys.argv[2]
    max_snaps = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    os.makedirs(out_dir, exist_ok=True)

    model = YOLO("yolov8s-pose.pt")
    manifest = []
    snap_id = 0

    # Sample ~2 FPS and keep the clearest single-player crops, spread across the clip
    for ts, frame in ex.frames(video, target_fps=2.0):
        if snap_id >= max_snaps:
            break
        r = model.predict(frame, device=_device(), conf=0.5, verbose=False)[0]
        if r.keypoints is None:
            continue
        xy = r.keypoints.xy.cpu().numpy()
        kconf = r.keypoints.conf.cpu().numpy() if r.keypoints.conf is not None else None
        boxes = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else None
        bconf = r.boxes.conf.cpu().numpy() if r.boxes is not None else None
        if xy.ndim != 3 or xy.shape[0] == 0 or xy.shape[1] < 17 or boxes is None:
            continue

        annotated = r.plot()  # BGR full frame with skeletons drawn
        h, w = annotated.shape[:2]

        # A coachable snapshot is a FULL-BODY action pose, not a face close-up.
        # Require shoulders + at least one hip + at least one knee/ankle visible.
        def full_body(i):
            def seen(j):
                return kconf is None or kconf[i][j] > 0.3
            shoulders = seen(5) or seen(6)
            hips = seen(11) or seen(12)
            legs = seen(13) or seen(14) or seen(15) or seen(16)
            box_h = boxes[i][3] - boxes[i][1]
            box_w = boxes[i][2] - boxes[i][0]
            tall = box_h >= 90 and box_h > box_w        # standing, not a head-crop
            return shoulders and hips and legs and tall

        # Keep every full-body player in this frame (spread across the clip)
        for i in range(len(boxes)):
            if snap_id >= max_snaps:
                break
            if not full_body(i):
                continue
            x1, y1, x2, y2 = boxes[i]
            pad = 15
            cx1, cy1 = max(0, int(x1 - pad)), max(0, int(y1 - pad))
            cx2, cy2 = min(w, int(x2 + pad)), min(h, int(y2 + pad))
            crop = annotated[cy1:cy2, cx1:cx2]
            if crop.size == 0:
                continue
            fn = f"snap_{snap_id:03d}.jpg"
            cv2.imwrite(os.path.join(out_dir, fn), crop, [cv2.IMWRITE_JPEG_QUALITY, 88])
            kpts = [[round(float(xy[i][j][0]), 1), round(float(xy[i][j][1]), 1),
                     round(float(kconf[i][j]), 3) if kconf is not None else 1.0] for j in range(17)]
            manifest.append({
                "id": fn,
                "source_frame_sec": round(ts, 2),
                "bbox": [round(float(v), 1) for v in (x1, y1, x2, y2)],
                "keypoints": kpts,
            })
            snap_id += 1

    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    # Make the folder self-contained for coach handover
    import shutil
    tool = os.path.join(os.path.dirname(__file__), "coach_pose_review.html")
    if os.path.exists(tool):
        shutil.copy(tool, out_dir)

    print(f"Wrote {snap_id} snapshots + manifest.json + coach_pose_review.html to {out_dir}")
    print("Coach handover: zip that folder, then in it run  python3 -m http.server 8000")
    print("and open  http://localhost:8000/coach_pose_review.html")


if __name__ == "__main__":
    main()
