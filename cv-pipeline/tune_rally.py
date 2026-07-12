#!/usr/bin/env python3
"""
Rally-threshold tuner — fit speed_threshold & min_duration to a REAL match.

Tonight's workflow (turns guess-and-check into a 5-minute data fit):
  1. Run the pipeline on the calibrated match → you get positions.json.
  2. Watch the match; jot down a handful of REAL rally start/end times (seconds)
     into marks.json, e.g.  [[132,151],[210,228],[402,447]]
  3. python3 tune_rally.py positions.json marks.json
     → it sweeps the thresholds and prints the settings that best reproduce your
       marked rallies (precision / recall / F1), so you pick the winner.

A detected window "matches" a marked rally if they overlap (IoU >= MIN_IOU).
"""

import json
import sys

import rally as rl

MIN_IOU = 0.3
SPEED_GRID = [round(0.2 + 0.1 * i, 1) for i in range(15)]   # 0.2 .. 1.6
DUR_GRID = [2.0, 3.0, 4.0, 5.0]


def iou(a, b):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    inter = max(0.0, hi - lo)
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    return inter / union if union > 0 else 0.0


def score(detected, marks):
    det = [(w.start_sec, w.end_sec) for w in detected]
    matched_marks = set()
    tp = 0
    for d in det:
        hit = False
        for i, m in enumerate(marks):
            if iou(d, m) >= MIN_IOU:
                hit = True
                matched_marks.add(i)
        tp += 1 if hit else 0
    precision = tp / len(det) if det else 0.0
    recall = len(matched_marks) / len(marks) if marks else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1, len(det)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    positions = json.load(open(sys.argv[1]))
    marks = json.load(open(sys.argv[2]))
    print(f"{len(positions)} position rows · {len(marks)} marked rallies\n")

    results = []
    for sp in SPEED_GRID:
        for du in DUR_GRID:
            windows = rl.detect(positions, min_duration=du, speed_threshold=sp)
            p, r, f, n = score(windows, marks)
            results.append((f, p, r, n, sp, du))

    results.sort(reverse=True)
    print(f"{'speed':>6} {'min_dur':>8} {'detected':>9} {'prec':>6} {'recall':>7} {'F1':>6}")
    print("-" * 50)
    for f, p, r, n, sp, du in results[:8]:
        print(f"{sp:>6} {du:>8} {n:>9} {p:>6.2f} {r:>7.2f} {f:>6.2f}")
    best = results[0]
    print(f"\nBEST → speed_threshold={best[4]}, min_duration={best[5]}  (F1={best[0]:.2f})")
    print("Set these in handler.py's rl.detect(...) call, or pass through.")


if __name__ == "__main__":
    main()
