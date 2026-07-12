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

def _device():
    import torch
    if torch.cuda.is_available(): return "cuda"
    if torch.backends.mps.is_available(): return "mps"
    return "cpu"

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

def top_striker(frame):
    cands = [(strike_score(k), k, b) for k, b in poses(frame) if full_body(k, b)]
    return max(cands, key=lambda c: c[0]) if cands else None

def nearest_player(frame, ref_box):
    cx, cy = (ref_box[0]+ref_box[2])/2, (ref_box[1]+ref_box[3])/2
    best, bd = None, 1e9
    for k, b in poses(frame):
        if not full_body(k, b): continue
        d = math.hypot((b[0]+b[2])/2 - cx, (b[1]+b[3])/2 - cy)
        if d < bd: bd, best = d, (k, b)
    return best

def draw(img, k, ox, oy, scale):
    H = img.shape[0]
    lw = max(2, int(H*0.010)); r = max(3, int(H*0.012))
    def P(j):
        x, y, c = k[j]
        return (int((x-ox)*scale), int((y-oy)*scale)) if c > KV else None
    for (a, b), col in LIMBS:
        pa, pb = P(a), P(b)
        if pa and pb:
            cv2.line(img, pa, pb, (20,20,20), lw+2); cv2.line(img, pa, pb, col, lw)
    for j in range(17):
        p = P(j)
        if p:
            cv2.circle(img, p, r+1, (20,20,20), -1)
            cv2.circle(img, p, r, (80,160,255) if j in (9,10) else (255,255,255), -1)

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
    # Pass 1 — strike-score series (no frame storage)
    series = []
    for t, frame in ex.frames(video, target_fps=10.0):
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
            manifest.append({"shot_id": shot_id, "shot_index": len(manifest)+1,
                             "peak_sec": round(pt,2), "strike_score": round(psc,2),
                             "front_facing": pface >= 2, "phases": phases})
    cap.release()


def main():
    # Usage: pose_label_gen.py <out_dir> <max_shots_per_clip> <video1> [video2 ...]
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
