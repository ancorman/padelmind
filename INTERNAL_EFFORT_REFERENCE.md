# Internal Effort Reference — Phase 1

**DO NOT SHARE.** This is our internal benchmark. Sent to no one.
Use this to sanity-check whatever Sasank returns.

Generated: 2026-07-09

---

## Our Estimates by Component

| Component | Task | Complexity | Our Days | Our Reasoning |
|---|---|---|---|---|
| **1 — Pi Edge** | MediaMTX install + RTSP relay config | L | 0.5 | Single YAML, binary service |
| | HTTP endpoint /match/start /match/stop | L | 0.5 | Flask, 30 lines |
| | Chunk detection + ffmpeg concat | M | 1.5 | Scan dir, concat, handle partial chunk |
| | Motion-based fallback end detection | M | 1.5 | Frame diff threshold, configurable |
| | R2 upload via boto3 + retry | L | 1.0 | Standard S3-compatible pattern |
| | Webhook POST on upload complete | L | 0.5 | Single HTTP POST |
| | systemd service + auto-restart | L | 0.5 | Standard unit file |
| | Integration test camera → R2 | M | 1.0 | Requires live camera |
| | **Subtotal** | | **7.0** | |
| **2 — GPU Worker** | Fork padel_analytics, strip UI | L | 0.5 | Remove app.py/ui.py |
| | Docker CUDA 12 + all deps | M | 1.0 | Layer ordering, first build slow |
| | RunPod HTTP endpoint | L | 0.5 | Documented pattern |
| | R2 video download | L | 0.5 | boto3 download_file |
| | Keypoints → homography matrix | L | 0.5 | Already in projected_court.py |
| | YOLOv8m + ByteTrack headless | M | 2.0 | Remove UI calls, add frame-stride |
| | Position projection per frame | M | 1.0 | Player.projection already wired |
| | Output positions JSON → R2 | L | 0.5 | Standard JSON + boto3 |
| | R2 upload all outputs | L | 0.5 | Same pattern as Pi |
| | Callback POST to our webhook | L | 0.5 | Single HTTP POST |
| | Perf tuning: 90min < 6min RTX 3090 | H | 2.0 | Frame-stride profiling |
| | Integration test on test video | M | 1.5 | We provide video + keypoints |
| | **Subtotal** | | **11.0** | |
| **3 — Heatmap** | Court diagram base (matplotlib) | L | 0.5 | 6H + 2V lines, fixed dims |
| | Gaussian heatmap from positions | L | 1.0 | histogram2d + gaussian_filter |
| | 4-player PNG, dark bg, fire cmap | L | 0.5 | Loop + savefig per player |
| | Player label + side annotation | L | 0.3 | ax.set_title, avg x-position |
| | File size < 300KB tuning | L | 0.2 | dpi=120, optimize=True |
| | Inline in RunPod worker | L | 0.5 | Function call post-tracking |
| | Integration test visual spot-check | L | 0.5 | Do hot-zones match footage? |
| | **Subtotal** | | **3.5** | |
| **4 — Rally Detector** | Per-player velocity computation | M | 1.0 | Sliding window, missing frames |
| | Rally state machine (LIVE/REST) | M | 1.0 | Two configurable thresholds |
| | Min duration filter (3s) | L | 0.3 | One filter pass |
| | Short-gap merger (30s) | M | 0.5 | Merge adjacent windows |
| | False positive suppression | M | 0.7 | < 2 players = not a rally |
| | Output top-8 windows | L | 0.3 | Sort + slice |
| | Integration test + threshold tuning | M | 1.5 | Watch video, 2-3 iterations |
| | **Subtotal** | | **5.3** | |
| **5 — Clipper** | Per-rally clip extraction | L | 0.5 | stream copy, fast |
| | 9:16 crop 1080×1920 | L | 0.5 | scale + crop filter |
| | Fade in/out 0.2s | L | 0.3 | fade filter |
| | Multi-clip concat | L | 0.5 | concat demuxer |
| | File size < 15MB CRF tuning | M | 0.7 | Varies by content |
| | Inline in RunPod worker | L | 0.3 | Sequential after C4 |
| | Integration test < 15MB watchable | L | 0.7 | Send to WA test number |
| | **Subtotal** | | **3.5** | |
| **6 — Calibration** | Canvas frame upload + overlay | L | 0.5 | FileReader + drawImage |
| | 12-point sequential click handler | M | 1.0 | Canvas click, auto-advance |
| | Draggable marker refinement | M | 0.7 | mousedown/move/up hit-test |
| | Reference diagram sidebar | L | 0.3 | Static SVG |
| | Save POST to our endpoint | L | 0.3 | Single fetch POST |
| | Integration test → homography valid | M | 0.7 | We verify in worker |
| | **Subtotal** | | **3.5** | |
| **Integration** | Full pipeline smoke test | H | 3.0 | Pi→R2→RunPod→WA |
| | Bug-fix cycle post smoke | H | 3.0 | Boundary issues |
| | README + env var list | L | 1.0 | Ops requirement |
| | Handover call | L | 0.5 | 1-hour recorded |
| | **Subtotal** | | **7.5** | |

---

## Summary

| Component | Our Days | Our Weeks |
|---|---|---|
| 1 — Pi Edge Software | 7.0 | 1.4 |
| 2 — GPU Inference Worker | 11.0 | 2.2 |
| 3 — Heatmap Renderer | 3.5 | 0.7 |
| 4 — Rally Detector | 5.3 | 1.1 |
| 5 — ffmpeg Highlight Clipper | 3.5 | 0.7 |
| 6 — Court Calibration Tool | 3.5 | 0.7 |
| Integration + Buffer | 7.5 | 1.5 |
| **Total** | **41.3** | **~8.3 weeks** |

## What to Watch For

- If Sasank's total is < 15 days, probe Component 2 perf tuning and integration buffer — those are where things actually take time.
- If Sasank's total is > 60 days, ask him to break down which tasks are driving it — likely padding on well-understood L-complexity items.
- Expected range with AI-assisted development: **18–28 days** for a senior developer using Claude Code or Cursor on green-field code. Our 41-day estimate assumed traditional development. With AI tooling, factor ~0.5–0.6 multiplier on L and M items.
- The H-complexity items (perf tuning, integration smoke test) are less compressible by AI tooling — keep those at face value.
