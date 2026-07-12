import os
import json
import tempfile
import requests
import runpod
from collections import defaultdict

import r2
import extract as ex
import detect as det
import track as tr
import heatmap as hm
import rally as rl
import highlight as hl
import stats as st
from homography import CourtHomography

WORKER_URL     = "https://padelmind-api.manoj-5ce.workers.dev"
RUNPOD_SECRET  = os.environ["RUNPOD_SHARED_SECRET"]
WARMUP_SEC     = 60.0   # seconds used to assign player slots


def handler(job: dict) -> dict:
    inp        = job["input"]
    match_id   = inp["match_id"]
    video_key  = inp["video_r2_key"]
    keypoints  = inp.get("keypoints")         # may be None before calibration
    slot_phones = inp.get("player_slots", {}) # {slot_str: phone}

    print(f"[{match_id}] Starting CV pipeline")

    with tempfile.TemporaryDirectory() as tmp:
        # ── 1. Download video ──────────────────────────────────────────────
        video_path = os.path.join(tmp, "match.mp4")
        print(f"[{match_id}] Downloading {video_key}")
        r2.download(video_key, video_path)

        duration_sec = ex.total_duration(video_path)
        print(f"[{match_id}] Duration: {duration_sec:.0f}s")

        # ── 2. Set up homography ───────────────────────────────────────────
        homo = CourtHomography(keypoints)
        if not homo.calibrated:
            print(f"[{match_id}] No calibration data — heatmaps will be skipped")

        # ── 3. Detect + track + project ───────────────────────────────────
        tracker = tr.build_tracker()
        position_log: list[dict] = []
        warmup_history: dict[int, list[tuple[float, float]]] = defaultdict(list)
        slot_map: dict[int, int] = {}

        for timestamp, frame in ex.frames(video_path, target_fps=5.0):
            detections = det.detect_players(frame)
            tracked    = tr.update(tracker, detections)

            for t in tracked:
                court_pt = homo.project(*t["foot"]) if homo.calibrated else None

                if court_pt:
                    cx, cy = court_pt

                    # Warmup slot assignment
                    if timestamp < WARMUP_SEC:
                        warmup_history[t["track_id"]].append((cx, cy))

                    position_log.append({
                        "timestamp":  timestamp,
                        "track_id":   t["track_id"],
                        "court_x":    cx,
                        "court_y":    cy,
                    })

            # Finalise slot assignment once warmup window passes
            if not slot_map and timestamp >= WARMUP_SEC and warmup_history:
                slot_map = tr.assign_slots(dict(warmup_history))
                print(f"[{match_id}] Slot map: {slot_map}")

        # Fallback if warmup window never filled (short match)
        if not slot_map and warmup_history:
            slot_map = tr.assign_slots(dict(warmup_history))

        # Add slot to position log
        for entry in position_log:
            entry["slot"] = slot_map.get(entry["track_id"], 0)

        # ── 4. Rally detection ────────────────────────────────────────────
        rallies = rl.detect(position_log)
        print(f"[{match_id}] {len(rallies)} rallies detected")

        # ── 4b. Phase 1.5 stats (distance, sprints, net %, fade) ─────────
        match_stats = st.compute(position_log, rallies, duration_sec) if homo.calibrated else {}
        print(f"[{match_id}] Stats computed for {len([k for k in match_stats if k.startswith('player')])} players")

        # ── 5. Highlight reel ─────────────────────────────────────────────
        highlight_key  = f"outputs/{match_id}/highlight.mp4"
        highlight_path = os.path.join(tmp, "highlight.mp4")
        highlight_ok   = hl.cut(video_path, highlight_path, rallies)
        if highlight_ok:
            r2.upload(highlight_path, highlight_key)

        # ── 6. Heatmaps ───────────────────────────────────────────────────
        heatmap_keys: dict[str, str] = {}
        if homo.calibrated:
            for slot in range(1, 5):
                pts = [(e["court_x"], e["court_y"]) for e in position_log if e["slot"] == slot]
                if not pts:
                    continue
                png_bytes = hm.generate(pts, player_name=f"Player {slot}")
                key = f"outputs/{match_id}/heatmap_p{slot}.png"
                r2.upload_bytes(png_bytes, key, "image/png")
                heatmap_keys[f"heatmap_p{slot}"] = key

        # ── 7. Positions JSON ─────────────────────────────────────────────
        positions_key = f"outputs/{match_id}/positions.json"
        r2.upload_bytes(
            json.dumps(position_log).encode(),
            positions_key,
            "application/json",
        )

        # ── 8. Callback to CF Worker ──────────────────────────────────────
        callback_body = {
            "secret":       RUNPOD_SECRET,
            "rally_count":  len(rallies),
            "duration_sec": int(duration_sec),
            "rally_windows": [r.to_dict() for r in rallies],
            "zones":        match_stats,  # Phase 1.5 stats — stored as zones_summary jsonb
            "outputs": {
                "heatmap_p1": heatmap_keys.get("heatmap_p1", ""),
                "heatmap_p2": heatmap_keys.get("heatmap_p2", ""),
                "heatmap_p3": heatmap_keys.get("heatmap_p3", ""),
                "heatmap_p4": heatmap_keys.get("heatmap_p4", ""),
                "highlight":  highlight_key if highlight_ok else "",
                "positions":  positions_key,
            },
        }
        resp = requests.post(
            f"{WORKER_URL}/api/matches/{match_id}/callback",
            json=callback_body,
            timeout=30,
        )
        print(f"[{match_id}] Callback: {resp.status_code}")

    return {
        "match_id":    match_id,
        "rally_count": len(rallies),
        "duration_sec": int(duration_sec),
        "heatmaps_generated": len(heatmap_keys),
        "highlight_ok": highlight_ok,
    }


runpod.serverless.start({"handler": handler})
