#!/usr/bin/env python3
"""Stage 2 + 4 — smooth the TrackNet track and project the ball onto the court.

Pipeline: TrackNet (motion ball detect) -> outlier-reject + gap-interpolate
(Stage 2) -> auto-calibration homography -> bounce detection -> project bounce
points to court coords -> top-down minimap (Stage 4).

Honest caveat: only BOUNCE points (ball on the ground plane) project accurately
through a ground homography; a ball in flight projected the same way is the
camera line-of-sight, not the true court position. So the minimap plots bounces.

Usage: python ball_court.py <video> <out.mp4> [start_frame] [n_frames]
"""
import sys, os
import cv2
import numpy as np
import torch
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "TrackNet"))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "cv-pipeline")))
from model import BallTrackerNet
from general import postprocess

VIDEO = sys.argv[1]
OUT = sys.argv[2]
START = int(sys.argv[3]) if len(sys.argv) > 3 else 0
N = int(sys.argv[4]) if len(sys.argv) > 4 else 260
W_IN, H_IN = 640, 360

dev = "mps" if torch.backends.mps.is_available() else "cpu"
model = BallTrackerNet()
model.load_state_dict(torch.load(os.path.join(HERE, "tracknet_tennis.pt"), map_location="cpu"))
model = model.to(dev)
model.train(False)

cap = cv2.VideoCapture(VIDEO)
fps = cap.get(cv2.CAP_PROP_FPS)
W = int(cap.get(3)); H = int(cap.get(4))
cap.set(cv2.CAP_PROP_POS_FRAMES, START)
frames = []
for _ in range(N):
    ok, f = cap.read()
    if not ok: break
    frames.append(f)
cap.release()
print(f"{len(frames)} frames {W}x{H}@{fps:.0f} dev={dev}")

# --- TrackNet raw track ---
sx, sy = W / 1280.0, H / 720.0
track = [(None, None)] * 2
with torch.no_grad():
    for i in range(2, len(frames)):
        trio = [cv2.resize(frames[j], (W_IN, H_IN)) for j in (i, i - 1, i - 2)]
        inp = np.rollaxis(np.concatenate(trio, axis=2).astype(np.float32) / 255.0, 2, 0)
        out = model(torch.from_numpy(inp[None]).float().to(dev))
        fmap = out.argmax(dim=1).detach().cpu().numpy().astype(np.float32)[0] / 255.0
        x, y = postprocess(fmap)
        track.append((x * sx if x else None, y * sy if y else None))
raw_det = sum(1 for p in track if p[0] is not None)
print(f"raw TrackNet: {raw_det}/{len(track)} = {100*raw_det/max(len(track),1):.0f}%")

# --- Stage 2: outlier reject + gap interpolate ---
xs = np.array([p[0] if p[0] is not None else np.nan for p in track])
ys = np.array([p[1] if p[1] is not None else np.nan for p in track])
MAXJUMP = 320  # px/frame — a ball can't teleport farther than this between frames
lastx = lasty = None
for i in range(len(xs)):
    if np.isnan(xs[i]):
        continue
    if lastx is not None and abs(xs[i] - lastx) + abs(ys[i] - lasty) > MAXJUMP * 2:
        xs[i] = ys[i] = np.nan
        continue
    lastx, lasty = xs[i], ys[i]

def interp_gaps(a, maxgap=7):
    a = a.copy()
    idx = np.where(~np.isnan(a))[0]
    for k in range(len(idx) - 1):
        i0, i1 = idx[k], idx[k + 1]
        if 1 < i1 - i0 <= maxgap + 1:
            a[i0:i1 + 1] = np.linspace(a[i0], a[i1], i1 - i0 + 1)
    return a

xs_s = interp_gaps(xs); ys_s = interp_gaps(ys)
det_s = int(np.sum(~np.isnan(xs_s)))
print(f"smoothed (Stage 2): {det_s}/{len(xs_s)} = {100*det_s/max(len(xs_s),1):.0f}%")

# --- Stage 4: homography ---
from auto_calibrate import auto_homography
from behind_court_cal import behind_court_homography
# YOLO net+serve-line calibration first; behind-court line solver as fallback
# (standard phone-behind-court angle hides the near serve line from YOLO).
H_mat = None
for fi in range(0, len(frames), 10):
    Hm, msg = auto_homography(frames[fi])
    if Hm is not None:
        H_mat = Hm; print(f"court calibrated (YOLO) frame {fi}: {msg}"); break
if H_mat is None:
    for fi in range(0, len(frames), 10):
        Hm, msg = behind_court_homography(frames[fi])
        if Hm is not None:
            H_mat = Hm; print(f"court calibrated (lines) frame {fi}: {msg}"); break
if H_mat is None:
    print("calibration failed on all scanned frames")

# bounce = local maximum in image-y (lowest visual point = ground contact)
bounces = []
for i in range(2, len(ys_s) - 2):
    seg = ys_s[i - 2:i + 3]
    if np.any(np.isnan(seg)):
        continue
    if ys_s[i] >= np.max(seg) - 1e-6 and ys_s[i] > ys_s[i - 2] and ys_s[i] > ys_s[i + 2]:
        bounces.append(i)
court_bounces = []
if H_mat is not None:
    for i in bounces:
        w = cv2.perspectiveTransform(np.float32([[[xs_s[i], ys_s[i]]]]), H_mat)[0][0]
        if -2 < w[0] < 12 and -2 < w[1] < 22:
            court_bounces.append((i, float(w[0]), float(w[1])))
print(f"bounces: {len(bounces)} detected, {len(court_bounces)} on-court")

# --- render camera overlay + top-down minimap inset ---
MM_S, MM_MX = 26, 22
mm_w = int(10 * MM_S + 2 * MM_MX); mm_h = int(20 * MM_S + 2 * MM_MX)
def mm_pt(wx, wy): return (int(MM_MX + wx * MM_S), int(MM_MX + wy * MM_S))
def minimap(active):
    mm = np.full((mm_h, mm_w, 3), 26, np.uint8)
    cv2.rectangle(mm, mm_pt(0, 0), mm_pt(10, 20), (180, 120, 60), 2)
    cv2.line(mm, mm_pt(0, 10), mm_pt(10, 10), (80, 220, 90), 2)
    for yy in (3, 17):
        cv2.line(mm, mm_pt(0, yy), mm_pt(10, yy), (200, 80, 200), 1)
    cv2.line(mm, mm_pt(5, 3), mm_pt(5, 17), (200, 80, 200), 1)
    for bi, wx, wy in court_bounces:
        col = (0, 255, 255) if bi == active else (90, 200, 255)
        cv2.circle(mm, mm_pt(wx, wy), 5, col, -1)
    cv2.putText(mm, "COURT top-down", (MM_MX, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (170, 170, 170), 1)
    return mm

bset = set(bounces)
vw = cv2.VideoWriter(OUT, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
trail = []
for i, f in enumerate(frames):
    x = xs_s[i] if i < len(xs_s) else np.nan
    y = ys_s[i] if i < len(ys_s) else np.nan
    if not np.isnan(x):
        trail.append((int(x), int(y)))
    trail = trail[-16:]
    for k, (tx, ty) in enumerate(trail):
        cv2.circle(f, (tx, ty), 3, (0, int(120 + 135 * (k + 1) / len(trail)), 255), -1)
    if not np.isnan(x):
        cv2.circle(f, (int(x), int(y)), 11, (0, 255, 0), 2)
    if i in bset and not np.isnan(x):
        cv2.circle(f, (int(x), int(y)), 20, (0, 255, 255), 3)
        cv2.putText(f, "BOUNCE", (int(x) + 22, int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    mm = minimap(i if i in bset else None)
    mh, mw = mm.shape[:2]
    f[10:10 + mh, W - 10 - mw:W - 10] = mm
    cv2.putText(f, f"Stage2 smooth + Stage4 court  f{START+i}", (20, 44),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    vw.write(f)
vw.release()
print("wrote", OUT)
