#!/usr/bin/env python3
"""
Phase 2b — generate coach labeling candidates as SHOT SEQUENCES.

A shot is not one frame — it is preparation -> backswing -> contact -> follow-
through. This detects each strike's peak and extracts the phases around it, so
the coach can rate the whole approach to the shot.

Two passes:
  1) score every frame's striking-player pose, find strike PEAKS (real shots).
  2) for each peak, grab the phase frames (by time offset), crop the same player,
     draw a bold skeleton, upscale.

Output:
  <out>/shot_XXX_pN.jpg   — phase images
  <out>/manifest.json     — [{shot_id, peak_sec, strike_score, front_facing,
                              phases:[{phase, id, t, keypoints}]}]

Usage:
  .venv/bin/python pose_label_gen.py <video> <out_dir> [max_shots]
"""

import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

import extract as ex

PHASES = [("Preparation", -0.70), ("Backswing", -0.35), ("Contact", 0.0), ("Follow-through", 0.45)]
KV = 0.3

LIMBS = [
    ((5, 7), (0, 220, 255)), ((7, 9), (0, 220, 255)),
    ((6, 8), (0, 220, 255)), ((8, 10), (0, 220, 255)),
    ((11, 13), (120, 230, 120)), ((13, 15), (120, 230, 120)),
    ((12, 14), (120, 230, 120)), ((14, 16), (120, 230, 120)),
    ((5, 6), (240, 240, 240)), ((11, 12), (240, 240, 240)),
    ((5, 11), (240, 240, 240)), ((6, 12), (240, 240, 240)),
]

_model = None
def model():
    global _model
    if _model is None:
        _model = YOLO("yolov8s-pose.pt")
    return _model

# MPS has a known YOLO-pose keypoint bug (produces the "impossibly long limb"
# artifacts). Use GPU only for fast peak-FINDING (pass 1); use CPU for the
# rendered skeletons the coach actually sees (pass 2) so keypoints are correct.
import torch
_GPU = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
DEVICE = _GPU

def _device():
    return DEVICE

def _pt(k, j):
    x, y, c = k[j]
    return (x, y) if c > KV else None

def strike_score(k):
    ls, rs, lh, rh = _pt(k,5), _pt(k,6), _pt(k,11), _pt(k,12)
    lw, rw = _pt(k,9), _pt(k,10)
    if not (ls and rs and lh and rh): return 0.0
    shm = ((ls[0]+rs[0])/2, (ls[1]+rs[1])/2)
    hpm = ((lh[0]+rh[0])/2, (lh[1]+rh[1])/2)
    torso = math.hypot(shm[0]-hpm[0], shm[1]-hpm[1]) or 1.0
    best = 0.0
    for sh, wr in ((ls, lw), (rs, rw)):
        if not wr: continue
        raised = (sh[1]-wr[1]) / torso                    # overhead component
        extend = math.hypot(wr[0]-sh[0], wr[1]-sh[1]) / torso  # reach — catches drives too
        best = max(best, max(0.0, raised)*1.4 + extend*1.1)
    return best

def face_score(k):
    return sum(1 for j in (0,1,2,3,4) if k[j][2] > KV)   # 0..5, higher = facing camera

def full_body(k, box):
    seen = lambda j: k[j][2] > KV
    bh, bw = box[3]-box[1], box[2]-box[0]
    return (seen(5) or seen(6)) and (seen(11) or seen(12)) and \
           (seen(13) or seen(14) or seen(15) or seen(16)) and bh >= 60 and bh > bw*0.7

def poses(frame):
    r = model().predict(frame, device=_device(), conf=0.5, verbose=False)[0]
    if r.keypoints is None: return []
    xy = r.keypoints.xy.cpu().numpy()
    kc = r.keypoints.conf.cpu().numpy() if r.keypoints.conf is not None else None
    boxes = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else None
    if xy.ndim != 3 or xy.shape[0] == 0 or xy.shape[1] < 17 or boxes is None: return []
    out = []
    for i in range(len(boxes)):
        k = [[float(xy[i][j][0]), float(xy[i][j][1]),
              float(kc[i][j]) if kc is not None else 1.0] for j in range(17)]
        out.append((k, boxes[i]))
    return out

# When PREFER_FRONT is on, target the front-facing person (e.g. the coach across
# the net whose face is visible) rather than the biggest/nearest player.
PREFER_FRONT = False

def top_striker(frame):
    cands = [(strike_score(k), k, b) for k, b in poses(frame) if full_body(k, b)]
    if not cands:
        return None
    if PREFER_FRONT:
        front = [c for c in cands if face_score(c[1]) >= 3]   # nose + eyes visible
        if front:
            cands = front
    return max(cands, key=lambda c: c[0])

def nearest_player(frame, ref_box):
    cx, cy = (ref_box[0]+ref_box[2])/2, (ref_box[1]+ref_box[3])/2
    best, bd = None, 1e9
    for k, b in poses(frame):
        if not full_body(k, b): continue
        d = math.hypot((b[0]+b[2])/2 - cx, (b[1]+b[3])/2 - cy)
        if d < bd: bd, best = d, (k, b)
    return best

def draw(img, k, ox, oy, scale):
    H, W = img.shape[:2]
    # Thin, Padel-AI style — reads as data over the game, doesn't overpower the image
    lw = max(2, int(H*0.006)); r = max(2, int(H*0.008))
    def P(j):
        x, y, c = k[j]
        if c <= KV:
            return None
        px, py = int((x-ox)*scale), int((y-oy)*scale)
        # Reject keypoints that fall well outside the crop (bad detections)
        if px < -W*0.15 or px > W*1.15 or py < -H*0.15 or py > H*1.15:
            return None
        return (px, py)

    # Torso length as the anatomical yardstick — a real limb segment never exceeds
    # ~1.3x the torso, so anything longer is a mis-detected joint: skip it.
    ls, rs, lh, rh = P(5), P(6), P(11), P(12)
    def mid(a, b): return ((a[0]+b[0])/2, (a[1]+b[1])/2) if a and b else None
    shm, hpm = mid(ls, rs), mid(lh, rh)
    torso = math.hypot(shm[0]-hpm[0], shm[1]-hpm[1]) if (shm and hpm) else H*0.35
    max_seg = max(H*0.12, torso*1.35)

    drawn = set()
    for (a, b), col in LIMBS:
        pa, pb = P(a), P(b)
        if pa and pb and math.hypot(pa[0]-pb[0], pa[1]-pb[1]) <= max_seg:
            cv2.line(img, pa, pb, (20,20,20), lw+2); cv2.line(img, pa, pb, col, lw)
            drawn.add(a); drawn.add(b)
    for j in drawn:                      # only joints that belong to a valid limb
        p = P(j)
        if p:
            cv2.circle(img, p, r+1, (20,20,20), -1)
            cv2.circle(img, p, r, (80,160,255) if j in (9,10) else (255,255,255), -1)

def gif_for_shot(cap, peak_t, pbox, out_path, target_h=260, nframes=16):
    """Render the shot as a looping slow-mo GIF with the skeleton overlaid, using
    a FIXED crop window (generous around the peak box) so the player doesn't jump."""
    x1, y1, x2, y2 = pbox
    padx, pady = (x2-x1)*0.75, (y2-y1)*0.45
    cap.set(cv2.CAP_PROP_POS_MSEC, peak_t*1000)
    ok, f0 = cap.read()
    if not ok:
        return None
    h, w = f0.shape[:2]
    cx1, cy1 = max(0, int(x1-padx)), max(0, int(y1-pady))
    cx2, cy2 = min(w, int(x2+padx)), min(h, int(y2+pady))
    frames = []
    for tt in np.linspace(peak_t-0.7, peak_t+0.5, nframes):
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, tt)*1000)
        ok, frame = cap.read()
        if not ok:
            continue
        crop = frame[cy1:cy2, cx1:cx2]
        if crop.size == 0:
            continue
        scale = max(1.0, target_h/crop.shape[0])
        crop = cv2.resize(crop, (int(crop.shape[1]*scale), int(crop.shape[0]*scale)), interpolation=cv2.INTER_CUBIC)
        crop = cv2.bilateralFilter(crop, 5, 50, 50)
        found = nearest_player(frame, pbox)
        if found:
            draw(crop, found[0], cx1, cy1, scale)
        frames.append(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)))
    if len(frames) < 4:
        return None
    frames[0].save(out_path, save_all=True, append_images=frames[1:],
                   duration=90, loop=0, optimize=True)
    return os.path.basename(out_path)


def crop_phase(frame, k, box, out_path):
    x1, y1, x2, y2 = box
    padx, pady = (x2-x1)*0.4, (y2-y1)*0.25
    h, w = frame.shape[:2]
    cx1, cy1 = max(0,int(x1-padx)), max(0,int(y1-pady))
    cx2, cy2 = min(w,int(x2+padx)), min(h,int(y2+pady))
    crop = frame[cy1:cy2, cx1:cx2]
    if crop.size == 0: return None
    scale = max(1.0, 480/crop.shape[0])
    crop = cv2.resize(crop, (int(crop.shape[1]*scale), int(crop.shape[0]*scale)), interpolation=cv2.INTER_CUBIC)
    crop = cv2.bilateralFilter(crop, 7, 60, 60)
    draw(crop, k, cx1, cy1, scale)
    cv2.imwrite(out_path, crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return [[round(v[0],1), round(v[1],1), round(v[2],3)] for v in k]

def process(video, out_dir, cidx, max_shots, manifest):
    global DEVICE
    DEVICE = _GPU                        # fast peak-finding
    # Pass 1 — strike-score series (no frame storage). 6 FPS is plenty to catch
    # a ~1s strike; keeps a 76-min clip tractable.
    series = []
    for t, frame in ex.frames(video, target_fps=6.0):
        top = top_striker(frame)
        series.append((t, top[0], top[2], face_score(top[1])) if top else (t, 0.0, None, 0))

    peaks, win = [], 0.4
    for t, sc, b, f in series:
        if sc < 1.5 or b is None: continue
        if sc >= max(s for (tt, s, _, _) in series if abs(tt - t) <= win):
            peaks.append((t, sc, b, f))
    peaks.sort(key=lambda p: p[1], reverse=True)
    chosen, used = [], []
    for p in peaks:
        if len(chosen) >= max_shots: break
        if all(abs(p[0]-u) >= 1.3 for u in used):
            chosen.append(p); used.append(p[0])
    chosen.sort(key=lambda p: p[0])

    # Pass 2 renders the skeletons the coach sees — switch to CPU for correct keypoints
    DEVICE = "cpu"
    cap = cv2.VideoCapture(video)
    for si, (pt, psc, pbox, pface) in enumerate(chosen):
        shot_id = f"c{cidx}s{si}"
        phases = []
        for pi, (pname, off) in enumerate(PHASES):
            tt = max(0.0, pt + off)
            cap.set(cv2.CAP_PROP_POS_MSEC, tt*1000)
            ok, frame = cap.read()
            if not ok: continue
            found = nearest_player(frame, pbox)
            if not found: continue
            k, b = found
            fn = f"{shot_id}_p{pi}.jpg"
            kp = crop_phase(frame, k, b, os.path.join(out_dir, fn))
            if kp: phases.append({"phase": pname, "id": fn, "t": round(tt,2), "keypoints": kp})
        if len(phases) >= 3:
            gif = gif_for_shot(cap, pt, pbox, os.path.join(out_dir, f"{shot_id}.gif"))
            manifest.append({"shot_id": shot_id, "shot_index": len(manifest)+1,
                             "peak_sec": round(pt,2), "strike_score": round(psc,2),
                             "front_facing": pface >= 2, "gif": gif, "phases": phases})
    cap.release()


def main():
    # Usage: PREFER_FRONT=1 pose_label_gen.py <out_dir> <max_shots_per_clip> <video1> [video2 ...]
    global PREFER_FRONT
    PREFER_FRONT = os.environ.get("PREFER_FRONT") == "1"
    out_dir = sys.argv[1]
    max_shots = int(sys.argv[2])
    videos = sys.argv[3:]
    os.makedirs(out_dir, exist_ok=True)
    manifest = []
    for cidx, video in enumerate(videos):
        process(video, out_dir, cidx, max_shots, manifest)
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {len(manifest)} shots ({sum(len(s['phases']) for s in manifest)} phase frames) to {out_dir}")


if __name__ == "__main__":
    main()
