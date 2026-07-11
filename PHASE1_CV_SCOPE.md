# PadelMind Phase 1 — CV Pipeline Scope
**Owner:** Manoj + Claude Code (replacing Sasank dependency)  
**Date:** 2026-07-11  
**Status:** SCOPED — pending Sunday test recording

---

## What this builds

Takes a raw padel match MP4 → produces:
1. Per-player heatmap PNGs (4 players)
2. Highlight clip MP4 (top rallies)
3. Rally list (start/end timestamps)
4. Player court positions JSON (for future analytics)

Runs as a RunPod serverless worker. Already integrates with the Phase 0 Worker queue — no new API surface needed.

---

## Mac Mini resource verdict: ✅ CAPABLE

| Resource | Required | Available | Verdict |
|---|---|---|---|
| Python | 3.10+ | 3.14.5 | ✅ |
| PyTorch | 2.0+ | 2.12.0 | ✅ |
| Metal GPU (MPS) | preferred | **Available** | ✅ YOLOv8 uses M2 GPU |
| RAM | ~3 GB peak | 8 GB | ✅ headroom to spare |
| Disk (dev/test) | ~10 GB | ~21 GB free | ✅ tight but OK |
| NumPy | required | NOT installed | ⚠️ install needed |
| ultralytics | required | NOT installed | ⚠️ install needed |
| OpenCV | required | NOT installed | ⚠️ install needed |

**Processing time estimate on Mac (90-min match, 5 FPS sampling):**
- Frame count: ~27,000 frames to process
- YOLOv8n on MPS: ~20-25 FPS → ~18-22 min total
- Perfectly fine for local dev/testing and overnight runs

**Production (RunPod A4000 GPU):** same job in ~2-3 min.

---

## Architecture

```
R2 (raw MP4)
    ↓ download
[Frame Extractor] → frames @ 5 FPS
    ↓
[Player Detector] → YOLOv8n, person class, MPS/CUDA
    ↓
[Player Tracker] → ByteTrack → 4 persistent track IDs
    ↓
[Slot Assigner] → track_id → slot 1/2/3/4 (court-half heuristic)
    ↓
[Homography] → OpenCV findHomography → camera px → court metres
    ↓
[Position Logger] → {frame, slot, court_x, court_y} for every frame
    ↙              ↘
[Heatmap Gen]    [Rally Detector]
4 PNG files      activity heuristic → rally windows
                       ↓
                 [Highlight Cutter]
                 ffmpeg → highlight.mp4
    ↓
Upload all outputs → R2
    ↓
POST /api/matches/:id/callback → CF Worker → DB update
```

---

## Module breakdown

### M1 — Frame Extractor
- OpenCV `VideoCapture` → extract every 6th frame (5 FPS from 30 FPS source)
- Tag each frame with `timestamp_sec = frame_idx / source_fps`
- Output: generator of `(timestamp, np.ndarray)`
- ~10 lines of code

### M2 — Player Detector  
- `ultralytics YOLOv8n` (nano model, 6 MB download)
- Device: `mps` on Mac, `cuda` on RunPod
- Filter: only `person` class (class_id = 0), confidence > 0.4
- Court mask: ignore detections outside court bounding box (set once per court using keypoints)
- Output: list of bounding boxes per frame

### M3 — Player Tracker
- `supervision` library ByteTrack wrapper
- Assigns persistent `tracker_id` to each player across frames
- Handles brief occlusions (player behind another, net, etc.)
- Output: `tracker_id → [(timestamp, bbox_centre)]` dict

### M4 — Slot Assigner
- Problem: which of 4 track_ids is player slot 1/2/3/4?
- Strategy: use first 60 seconds of match (warm-up/positioning)
  - Project each tracker's average position through homography
  - Near half (y < 10m): slots 1 & 2; Far half (y > 10m): slots 3 & 4
  - Within each half, left (x < 5m) = odd slot, right (x > 5m) = even slot
- Output: `{tracker_id: slot}` mapping (stable for the match)
- Edge case: player crosses to other half temporarily — use rolling 10-sec average

### M5 — Court Homography
- Load `camera_keypoints` from Supabase (already calibrated via P0-G tool)
- Camera points: 12 pixel coords from our calibration tool
- World points: fixed padel court coordinates (metres)
  ```
  Point 1: (0, 0)     ← near-left corner
  Point 2: (10, 0)    ← near-right corner
  Point 3: (0, 3)     ← near service line left
  Point 4: (10, 3)    ← near service line right
  Point 5: (5, 3)     ← center T near
  Point 6: (0, 10)    ← net left
  Point 7: (10, 10)   ← net right
  Point 8: (0, 17)    ← far service line left
  Point 9: (10, 17)   ← far service line right
  Point 10: (5, 17)   ← center T far
  Point 11: (0, 20)   ← far-left corner
  Point 12: (10, 20)  ← far-right corner
  ```
- `H, _ = cv2.findHomography(cam_pts, world_pts)`
- For each player foot position: `court_pt = H @ [px, py, 1]` → normalise
- Output: court (x, y) in metres for every player at every timestamp

### M6 — Heatmap Generator
- Aggregate `(court_x, court_y)` per slot → 2D histogram (100×200 grid)
- Render: court diagram (white) + coloured heatmap overlay (matplotlib `imshow`, colormap `hot`)
- Save as PNG → upload to R2 `outputs/{match_id}/heatmap_p{slot}.png`
- One PNG per player, total 4 PNGs

### M7 — Rally Detector
- No ball tracking needed. Heuristic:
  - Compute average player speed (court metres/sec) in each half per 1-sec window
  - Rally condition: both halves have avg speed > threshold (0.5 m/s) for ≥ 3 consecutive seconds
  - Rally ends when either half drops below threshold for 2 consecutive seconds
- Post-process: merge rallies < 1 sec apart, drop rallies < 3 sec
- Output: `[{start_sec, end_sec, duration_sec}]`

### M8 — Highlight Cutter
- Select top 5 rallies by duration (or all if < 8 rallies)
- Add 1-second padding on each side
- ffmpeg: cut each segment → concatenate → re-encode H.264
- Save as `outputs/{match_id}/highlight.mp4` → upload to R2

### M9 — RunPod Handler (entry point)
```python
def handler(job):
    input = job['input']
    match_id = input['match_id']
    video_key = input['video_r2_key']
    keypoints = input['keypoints']
    player_slots = input['player_slots']  # {slot: phone}

    # download MP4 from R2
    # run M1 → M8
    # upload outputs to R2
    # POST /api/matches/{match_id}/callback
```
- Auth: `RUNPOD_SHARED_SECRET` (already set in CF Worker)
- The CF Worker `/api/jobs/next` already returns `keypoints` and `player_slots` — M9 receives all it needs

---

## What we're NOT building (V1 skip list)

| Feature | Why skipped | V2 path |
|---|---|---|
| Ball tracking | Hard: small, fast, glass glare | Fine-tuned YOLO model |
| Serve/smash/volley classification | Needs pose estimation | MediaPipe Pose |
| Score tracking | No OCR on scoreboard | EasyOCR |
| Padel-specific model fine-tuning | YOLOv8 person class is sufficient for V1 | Roboflow dataset |

---

## Tech stack (all open-source, zero cost)

```
ultralytics        # YOLOv8, downloads model weights automatically
opencv-python      # homography, frame extraction
supervision        # ByteTrack player tracking
numpy              # math
matplotlib         # heatmap rendering
Pillow             # court diagram compositing
boto3              # R2 uploads (S3-compatible)
ffmpeg             # highlight cutting (system binary)
requests           # Worker callback
```

---

## Install (Mac dev environment)

```bash
pip3 install numpy ultralytics opencv-python supervision matplotlib Pillow boto3
```

YOLOv8n model downloads automatically on first run (~6 MB).

---

## Build order

| Step | What | Time |
|---|---|---|
| 1 | Install deps + smoke test YOLOv8 on MPS | 30 min |
| 2 | M1+M2: frame extraction + player detection on Sunday's video | 1-2 hrs |
| 3 | M3+M4: tracking + slot assignment | 1 day |
| 4 | M5: homography (needs Sunday calibration first) | 2-3 hrs |
| 5 | M6: heatmap generator | 2-3 hrs |
| 6 | M7+M8: rally detection + highlight cutter | 1 day |
| 7 | M9: RunPod handler + R2 upload + callback | 2-3 hrs |
| 8 | End-to-end test on Mac → then RunPod | 1 day |

**Total: 4-5 days of focused build after Sunday's recording**

---

## Dependency on Sunday

Step 4 (homography) requires the calibrated keypoints for NSCI Court 2.  
Steps 1-3 can start **before** Sunday using any test video (even a YouTube padel match).  
Steps 4-8 need Sunday's recording + calibration.

---

## RunPod setup (when ready for production)

- Serverless endpoint: RunPod `runpod/pytorch` base image
- GPU: A4000 (cheapest with enough VRAM for YOLOv8 + ByteTrack)
- Estimated cost: ~$0.0002/sec → 3-min job = ~$0.04/match
- The Worker queue (`/api/jobs/next`) already delivers the job payload — no new infra needed

---

## Files to create

```
padel-clone/
  cv-pipeline/
    __init__.py
    extract.py       # M1
    detect.py        # M2
    track.py         # M3+M4
    homography.py    # M5
    heatmap.py       # M6
    rally.py         # M7
    highlight.py     # M8
    r2.py            # R2 upload/download helpers
    handler.py       # M9 RunPod entry point
    test_local.py    # local end-to-end test script
  Dockerfile         # RunPod image
  requirements.txt
```
