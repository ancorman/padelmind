#!/usr/bin/env python3
"""
R5 benchmark — custom padel model vs stock YOLOv8n on real padel frames.

Usage (once per model, fresh process so the model cache is clean):
  YOLO_MODEL=yolov8n.pt .venv/bin/python bench_r5.py <video> <out_dir> stock
  YOLO_MODEL=models/padel_yolov8s_wpt_v11.pt .venv/bin/python bench_r5.py <video> <out_dir> custom

Prints per-model stats and saves 3 annotated sample frames for eyeballing.
"""

import json
import os
import sys
import time

import cv2

import detect as det
import extract as ex


def main():
    video, out_dir, tag = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)

    counts, confs = [], []
    samples_saved = 0
    t0 = time.time()
    n_frames = 0

    for timestamp, frame in ex.frames(video, target_fps=5.0):
        detections = det.detect_players(frame)
        n_frames += 1
        counts.append(len(detections))
        confs.extend(d["conf"] for d in detections)

        # save annotated samples at ~20s intervals
        if samples_saved < 3 and timestamp >= samples_saved * 20 + 10:
            vis = frame.copy()
            for d in detections:
                x1, y1, x2, y2 = map(int, d["bbox"])
                cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(vis, f'{d["conf"]:.2f}', (x1, y1 - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imwrite(os.path.join(out_dir, f"{tag}_sample{samples_saved + 1}.jpg"), vis)
            samples_saved += 1

    elapsed = time.time() - t0
    stats = {
        "model": os.environ.get("YOLO_MODEL", "yolov8n.pt"),
        "tag": tag,
        "frames": n_frames,
        "fps": round(n_frames / elapsed, 1),
        "avg_players_per_frame": round(sum(counts) / max(len(counts), 1), 2),
        "pct_frames_ge2_players": round(100 * sum(1 for c in counts if c >= 2) / max(len(counts), 1), 1),
        "pct_frames_ge4_players": round(100 * sum(1 for c in counts if c >= 4) / max(len(counts), 1), 1),
        "mean_conf": round(sum(confs) / max(len(confs), 1), 3),
    }
    print(json.dumps(stats, indent=2))
    with open(os.path.join(out_dir, f"{tag}_stats.json"), "w") as f:
        json.dump(stats, f, indent=2)


if __name__ == "__main__":
    main()
