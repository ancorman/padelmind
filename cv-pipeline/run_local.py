#!/usr/bin/env python3
"""
Local end-to-end harness — runs the FULL RunPod handler on a local video with
R2 + the callback stubbed out. Proves the whole chain
(extract→detect→track→homography→heatmap→rally→stats→output assembly) executes
and produces real output files, WITHOUT footage from the pilot, without RunPod,
without touching R2 or the Worker.

Usage:
  YOLO_MODEL=models/padel_yolov8s_wpt_v11.pt \
    .venv/bin/python run_local.py <video.mp4> <out_dir> [keypoints.json]

If no keypoints file is given, uses fabricated WPT-clip keypoints so the
homography/heatmap/stats path runs (coords approximate — this is an integration
test, not an accuracy test). For the real pilot, pass the calibration JSON.
"""

import json
import os
import shutil
import sys

os.environ.setdefault("RUNPOD_SHARED_SECRET", "local-harness")

# Fabricated keypoints roughly tracing the WPT test clip's court (1280x720),
# in the 12-point calibration order. Approximate — enough for a valid homography.
WPT_KEYPOINTS = {
    "image_width": 1280, "image_height": 720,
    "points": [
        {"n": 1,  "x": 300, "y": 600},  # near-left corner
        {"n": 2,  "x": 980, "y": 600},  # near-right corner
        {"n": 3,  "x": 315, "y": 528},  # near service line left
        {"n": 4,  "x": 965, "y": 528},  # near service line right
        {"n": 5,  "x": 640, "y": 528},  # center T near
        {"n": 6,  "x": 350, "y": 360},  # net left
        {"n": 7,  "x": 930, "y": 360},  # net right
        {"n": 8,  "x": 427, "y": 234},  # far service line left
        {"n": 9,  "x": 853, "y": 234},  # far service line right
        {"n": 10, "x": 640, "y": 234},  # center T far
        {"n": 11, "x": 460, "y": 180},  # far-left corner
        {"n": 12, "x": 820, "y": 180},  # far-right corner
    ],
}


def main():
    video, out_dir = sys.argv[1], sys.argv[2]
    keypoints = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else WPT_KEYPOINTS
    os.makedirs(out_dir, exist_ok=True)

    # ── Stub R2: download = local copy, uploads = write to out_dir ──────────
    import r2

    r2.download = lambda key, local: shutil.copy(video, local)

    def _upload(local_path, key):
        dst = os.path.join(out_dir, os.path.basename(key))
        shutil.copy(local_path, dst)
        print(f"  [upload] {key} -> {dst}")
        return dst

    def _upload_bytes(data, key, content_type="application/octet-stream"):
        dst = os.path.join(out_dir, os.path.basename(key))
        with open(dst, "wb") as f:
            f.write(data)
        print(f"  [upload_bytes] {key} -> {dst} ({len(data)} bytes)")
        return dst

    r2.upload = _upload
    r2.upload_bytes = _upload_bytes

    # ── Stub the Worker callback: capture the body instead of POSTing ──────
    import requests
    captured = {}

    class _Resp:
        status_code = 200

    def _post(url, json=None, timeout=None):
        captured["url"] = url
        captured["body"] = json
        return _Resp()

    requests.post = _post

    # ── Run the real handler ───────────────────────────────────────────────
    import handler

    job = {"input": {
        "match_id": "local-test",
        "video_r2_key": video,
        "keypoints": keypoints,
        "player_slots": {"1": "+910000000001", "2": "+910000000002",
                         "3": "+910000000003", "4": "+910000000004"},
    }}

    print("=== running handler ===")
    result = handler.handler(job)

    print("\n=== handler return ===")
    print(json.dumps(result, indent=2))

    print("\n=== captured callback body (what the Worker would store) ===")
    body = captured.get("body", {})
    # Trim the noisy fields for readability
    print(json.dumps({
        "rally_count": body.get("rally_count"),
        "duration_sec": body.get("duration_sec"),
        "n_rally_windows": len(body.get("rally_windows", [])),
        "zones_players": [k for k in body.get("zones", {}) if k.startswith("player")],
        "zones_sample": next((v for k, v in body.get("zones", {}).items()
                              if k.startswith("player")), None),
        "outputs": body.get("outputs"),
    }, indent=2))

    print("\n=== output files written ===")
    for fn in sorted(os.listdir(out_dir)):
        p = os.path.join(out_dir, fn)
        print(f"  {fn}  ({os.path.getsize(p)} bytes)")


if __name__ == "__main__":
    main()
