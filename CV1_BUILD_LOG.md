# PadelMind Phase 1 CV — "Our End" Build Log

**What:** Build the Phase-1 CV pipeline ourselves (Manoj + Claude Code), replacing the Sasank contractor dependency. Raw padel MP4 → 4 player heatmaps + highlight reel + rally list + positions JSON. Runs local (M2 Mac, dev) → RunPod (prod), feeding the existing Phase-0 Worker queue.

**Scope source of truth:** [PHASE1_CV_SCOPE.md](PHASE1_CV_SCOPE.md) (module + arch spec) and [SASANK_SOW_PHASE1.md](SASANK_SOW_PHASE1.md) (contractor version / integration contract).
**Feature roadmap / ship-now-vs-promise map:** [PHASE_FEATURE_MAP.md](PHASE_FEATURE_MAP.md) (added 2026-07-12 — Tier S/S+/P feature tiers, Phase-1.5 stats layer plan, coach MCQ workflow for pose validation).
**Recording field guide:** [NSCI_RECORDING_GUIDE.md](NSCI_RECORDING_GUIDE.md) (2026-07-12 — tonight's floodlight match: camera lock ritual, 30s empty-court calibration clip, drift check, optional daytime bonus clip). Calibration = ONE still from the locked recording camera + 10–15 min of clicking; NOT per-location stills.
**This file:** live execution log — updated as each step lands. One step at a time.

**Started:** 2026-07-12

---

## Environment baseline (verified 2026-07-12)

| Item | Value |
|---|---|
| Hardware | Apple M2 Mac mini, 8 GB unified memory |
| Disk free on `/` | ~23 GB (tight — watch it) |
| ffmpeg | 8.1.1 (`/opt/homebrew/bin/ffmpeg`) ✅ |
| System python (login shell) | 3.14.2 — has boto3/scipy/torch, NO ultralytics/supervision. **NOT our build target** (3.14 CV wheels unreliable) |
| `.reelpy` venv | 3.12.13 — AutomationXpert reel env. **Do NOT pollute.** |
| **Build target** | **Dedicated venv `cv-pipeline/.venv` on Python 3.12** (matches RunPod 3.11 far better than 3.14) |

## Storage convention (set 2026-07-12)

Internal disk is tight (~20 GB free, 96% full). **Bulk / occasional-use data → external disk.**
- **`PADEL_DATA_DIR=/Volumes/AXMedia/PadelMind/cv-data`** (external, 891 GB free) — `datasets/ videos/ models/ outputs/`.
- Code + venv stay on internal (`~/Documents/padel-clone/cv-pipeline`).
- ⚠️ External disk not always mounted — scripts using `PADEL_DATA_DIR` must check the mount exists and fail with a clear message if absent.

## Existing code state (from Jul 11 session)

`cv-pipeline/` already has full M1–M9 drafts: `extract.py detect.py track.py homography.py heatmap.py rally.py highlight.py r2.py handler.py requirements.txt`.
**Status: DRAFTED, never run.** The job now = stand up env → run → debug.

### Known issues spotted by reading (pre-run)
- `track.py`: uses `sv.ByteTracker` — correct class is `sv.ByteTrack`. Will fail on first run. Fix at Step 3.
- `r2.py` / `handler.py`: need env vars `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `RUNPOD_SHARED_SECRET`. Relevant at Step 7.
- Pre-calibration (no homography), `handler.py` only logs positions when `homo.calibrated` → pre-Sunday testing must exercise detect/track in **pixel space**, not the full handler.

---

## Step plan

| # | Step | Needs Sunday recording? | Status |
|---|---|---|---|
| 1 | Dedicated venv + install deps + YOLOv8 MPS smoke test | No | ✅ DONE |
| 2 | M1+M2 — frame extraction + player detection on a test video | No | ✅ DONE (90s WPT clip, 451 frames, both models) |
| 3 | M3+M4 — ByteTrack tracking + slot assignment (fix ByteTrack bug) | No | ✅ bug fixed (`sv.ByteTrack`) + smoke-tested; real-footage run pending |
| 4 | M5 — court homography (pixel→metres) | Yes (NSCI calibration) | ⬜ |
| 5 | M6 — per-player heatmap PNGs | Yes | ⬜ |
| 6 | M7+M8 — rally detection + ffmpeg highlight cutter | Yes | ⬜ |
| 7 | M9 — RunPod handler + R2 upload + Worker callback | No | ⬜ |
| 8 | End-to-end test: Mac → then RunPod | Yes | ⬜ |

**Today (pre-Sunday):** steps 1–3 are runnable. 4–8 need Sunday's NSCI Court-2 recording + calibration.

### Decision 2026-07-12 — Roboflow TRAINING track (chosen: "Training-focused")
Manoj chose to build a **custom padel detection model** (not just generic YOLOv8n person class). Rationale: padel's real failure modes (players packed close, glass-wall reflections, occlusion) hurt generic person detection. Custom weights drop into `detect.py` via `YOLO_MODEL` env var — zero code change. Ball tracking stays V2.

**Hardware rule: DO NOT train on the M2** (8 GB RAM — see [[reference_manoj_mac_hardware]]). Train on a rented/free GPU (Colab T4 free, or RunPod pod). M2 is for dataset prep + inference/eval only.

Roboflow sub-steps:
| # | Step | Status |
|---|---|---|
| R1 | Create Roboflow account + get Private API Key | ✅ DONE |
| R2 | Pick padel dataset(s) on Roboflow Universe (player-detection first) | ✅ DONE |
| R3 | `pip install roboflow`; download dataset in YOLOv8 format | ✅ DONE |
| R4 | Train custom YOLOv8 on GPU — **venue: Google Colab free T4** | ✅ DONE — 50 epochs, player mAP50 0.985, weights committed cv-pipeline/models/ |
| R5 | Download weights → set `YOLO_MODEL` → benchmark vs yolov8n on our footage | ✅ DONE — custom wins: ≥4 players 63.9% vs 49.0%, conf 0.889 vs 0.674, far-court +0.2, zero crowd FPs (`bench_r5.py`) |

**R1:** Roboflow account created (Google SSO). Premium Trial active — 14 days, **15 credits** (could fund a Roboflow-hosted training run). Key stored in git-ignored `cv-pipeline/.env` as `ROBOFLOW_API_KEY`. SDK roboflow 1.3.13 installed (note: downgraded opencv-headless 4.11→4.10, typer — harmless).
**R2:** Dataset = **`yolo-data-labeling/padel-wpt-10videos`** (multi-class: player 6152, racket 4076, serve line 3088, ball 2164, net 1545; 11 versions). Downloading v11 (yolov8 fmt) → `$PADEL_DATA_DIR/datasets/padel-wpt-10videos-v11`.
**Domain-gap caveat:** WPT = broadcast footage; our pilot cam is fixed overhead-behind-glass. Plan: bootstrap-train on this → fine-tune on annotated NSCI frames post-Sunday for real pilot accuracy.

**R3 result (2026-07-12):** v11 downloaded to external disk — 3,246 train / 308 valid / 155 test (3,709 imgs, 317 MB), 5 classes `ball,net,player,racket,serve line`, license **CC BY 4.0** (commercial OK w/ attribution). `data.yaml` YOLOv8-ready.
**R4 venue decision:** **Google Colab free T4** — $0, produces portable `best.pt` (no Roboflow inference-API lock-in), preserves 15 trial credits + RunPod budget for the post-Sunday NSCI fine-tune. Notebook: `cv-pipeline/colab_train_padel_yolov8.ipynb` (YOLOv8s, 50 epochs, patience 10, imgsz 640, batch 16; evaluates on held-out test split; auto-downloads `padel_yolov8s_wpt_v11.pt`). ⚠️ Notebook embeds the Roboflow key → git-ignored; do not share.
**R5 plan:** weights → `$PADEL_DATA_DIR/models/`, `YOLO_MODEL=<path>` env → benchmark vs stock yolov8n.

---

## Execution log

### Step 1 — venv + deps + YOLO MPS smoke test — ✅ DONE (2026-07-12)
- Dedicated venv created: `cv-pipeline/.venv`, Python 3.12.13, isolated (not `.reelpy`).
- **Dep conflict found + fixed:** `requirements.txt` pins `numpy==2.2.3`, but `ultralytics 8.3.40` caps `numpy<2.0.0` on darwin → `ResolutionImpossible` on Mac. The pin is correct for RunPod/Linux; created **`requirements-dev-mac.txt`** (numpy==1.26.4) for local Mac only. Prod `requirements.txt` left untouched — DO NOT put the mac file in the Docker image.
- Installed OK: torch 2.13.0, ultralytics 8.3.40, supervision 0.25.1, opencv-headless 4.11.0.86, numpy 1.26.4, matplotlib 3.10.1, boto3 1.37.20, runpod 1.7.9.
- **YOLOv8 MPS smoke test PASSED:** MPS available+built; YOLOv8n downloaded (6.25 MB) and ran on `mps`; 6.3 s cold-start (model load + first kernel compile), 0 boxes on noise (expected).
- **Step-3 bug confirmed:** `sv.ByteTrack` exists, `sv.ByteTracker` does NOT. track.py must switch class name. Valid init params: `track_activation_threshold, lost_track_buffer, minimum_matching_threshold, frame_rate, minimum_consecutive_frames`.

**Next: Step 2** — needs a padel test video (see open question below).

---

## Log — 2026-07-12 (evening session, main window)

- **Step 2 ✅ / R5 ✅**: `bench_r5.py` on 90s WPT 720p clip (451 frames @5FPS, MPS). Custom `padel_yolov8s_wpt_v11.pt`: all-4-players in 63.9% frames, mean conf 0.889, ignores crowd/replay close-ups. Stock yolov8n: 49.0%, conf 0.674, fires on spectators. Far-court players +0.2 conf with custom. Annotated frames: `$PADEL_DATA_DIR/outputs/bench_r5/`.
- **Step 3 code ✅**: `track.py` ByteTracker→ByteTrack fixed, 4-track smoke test green. Real-footage tracking run when NSCI recording lands.
- **Phase 1.5 stats layer built** (`stats.py` + 6 passing tests): distance/top-speed/sprints/net%/baseline%/zones/fade/longest-rally from positions JSON. Wired into `handler.py` callback `zones` field → lands in `padel_match_outputs.zones_summary` with zero Worker changes.
- **detect.py**: player class resolved by name (custom model is alphabetical — classes=[0] would have detected balls).
- **NEXT (needs tonight's footage):** calibrate Court 2 from empty-court still → Steps 4–6 on the real match → Step 7–8 E2E (Worker deploy + `YOLO_MODEL` env on RunPod = Manoj's go).

## Log — 2026-07-12 (late, cont.)

- **Phase 2 prototypes** (Tier P): `ball_track.py` (Kalman, works but ball detection only 15% on WPT clip — gated on a better ball model) + `pose.py` (YOLOv8-pose off-the-shelf, 100% coverage 28FPS, NO Roboflow data needed — the cheap Phase-2 win).
- **Local E2E harness** (`run_local.py`): whole handler runs offline (R2 + callback stubbed) → real heatmap PNG + highlight.mp4 + positions.json + correctly-shaped callback with Phase-1.5 stats. Integration VALIDATED end-to-end. Degenerate values are broadcast-footage + fake-keypoint artifacts, not bugs.
- **Fixed:** handler ran `runpod.serverless.start()` on import (now `__main__`-guarded). rally.py switched from positional-spread to velocity per SOW.
- **Flags for the real run:** (1) slot assignment gave 1/4 players on broadcast footage (camera cuts fragment ByteTrack) — watch it on real single-camera footage; (2) all thresholds (rally speed 0.5 m/s, sprint 3 m/s) need 2-3 tuning passes on a watched real match.
- **Footage-independent build queue now essentially exhausted.** Remaining: WA V1.5 message template wiring + PWA match report page (both "make stats visible" — best built against real stats), then the real-footage run (calibrate → run_local with real keypoints → RunPod).
