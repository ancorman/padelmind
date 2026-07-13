#!/usr/bin/env python3
"""Zero-shot TrackNet (tennis-pretrained) on padel footage.

The test that matters: on a drill clip with many STATIC balls on the court, does
a motion-based tracker lock onto the one MOVING ball and ignore the rest — the
thing an appearance detector (YOLO) structurally cannot do.

Usage: python run_tracknet.py <video> <out.mp4> [start_frame] [n_frames]
"""
import sys, os
import cv2
import numpy as np
import torch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "TrackNet"))
from model import BallTrackerNet
from general import postprocess

VIDEO = sys.argv[1]
OUT = sys.argv[2]
START = int(sys.argv[3]) if len(sys.argv) > 3 else 0
N = int(sys.argv[4]) if len(sys.argv) > 4 else 250
W_IN, H_IN = 640, 360

dev = "mps" if torch.backends.mps.is_available() else "cpu"
model = BallTrackerNet()
model.load_state_dict(torch.load(os.path.join(os.path.dirname(__file__), "tracknet_tennis.pt"), map_location="cpu"))
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
print(f"{len(frames)} frames  {W}x{H}@{fps:.0f}  device={dev}")

sx, sy = W / 1280.0, H / 720.0    # postprocess coords are in 1280x720
track = [(None, None)] * 2
with torch.no_grad():
    for i in range(2, len(frames)):
        trio = [cv2.resize(frames[j], (W_IN, H_IN)) for j in (i, i-1, i-2)]
        inp = np.rollaxis(np.concatenate(trio, axis=2).astype(np.float32) / 255.0, 2, 0)
        out = model(torch.from_numpy(inp[None]).float().to(dev))
        fmap = out.argmax(dim=1).detach().cpu().numpy().astype(np.float32)[0] / 255.0
        x, y = postprocess(fmap)
        track.append((x * sx if x else None, y * sy if y else None))

det = sum(1 for p in track if p[0] is not None)
print(f"ball found in {det}/{len(track)} frames = {100*det/len(track):.1f}%")

vw = cv2.VideoWriter(OUT, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
trace = []
for i, f in enumerate(frames):
    x, y = track[i] if i < len(track) else (None, None)
    if x is not None:
        trace.append((int(x), int(y)))
    trace = trace[-12:]
    for k, (tx, ty) in enumerate(trace):          # fading motion trail
        cv2.circle(f, (tx, ty), 4, (0, 165, 255), -1)
    if x is not None:
        cv2.circle(f, (int(x), int(y)), 12, (0, 255, 0), 3)
    cv2.putText(f, f"TrackNet (zero-shot tennis)  f{START+i}", (20, 44),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
    vw.write(f)
vw.release()
print("wrote", OUT)
