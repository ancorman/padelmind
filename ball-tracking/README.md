# Ball tracking — the tactical unlock

The ball, not the player, decides padel points. Tracking it is the gate between
the technique coach we can build now and the winning coach we want (serve
placement, shot selection, ball speed → the Tactics pillar of the Player Score).

## Why not YOLO
A ball is small, fast (motion-blurred to a streak), low-contrast, and vanishes
behind glass. Worse, on real Indian-court **drill footage there are 6–8 static
balls lying on the court** — an appearance detector can't tell a ball in flight
from one on the ground. Our custom YOLO ball class proves it: on `court1_wide_seg`
it reports a "ball" in 91% of frames but **423/632 frames are multi-ball** (mean
conf 0.38) — it boxes static decoys and reflections.

## The approach: TrackNet (motion-based heatmap CNN)
TrackNet eats **3 consecutive frames** and outputs a ball-position heatmap, so it
finds the ball **by its motion** and structurally ignores anything static.

### Result — zero-shot, tennis-pretrained, no padel fine-tuning
On `court1_wide_seg.mp4` (dim drill footage, ~7 static decoy balls):
- **71% of frames** get a ball point (vs YOLO's noisy multi-ball mess).
- It traces the **flight arc of the one moving ball and ignores every static
  one** — exactly what YOLO cannot do.

## Setup (not committed — large/vendored)
```
cd ball-tracking
git clone https://github.com/yastrebksv/TrackNet         # vendored, gitignored
pip install gdown && gdown "https://drive.google.com/uc?id=1XEYZ4myUN7QT-NeBYJI0xteLsvs-ZAOl" -O tracknet_tennis.pt
python run_tracknet.py <video> <out.mp4> [start_frame] [n_frames]
```
Runs on Apple MPS. `run_tracknet.py` is ours (committed); TrackNet/ and the
41 MB weights are gitignored.

## Next
1. Smooth the track — outlier removal + gap interpolation (TrackNet repo ships
   `remove_outliers` / `split_track` / `interpolation`); or feed into the
   existing `cv-pipeline/ball_track.py` Kalman.
2. Events — bounce (trajectory inflection + court-plane crossing) and hit
   (direction change at a player, correlated with the pose contact frame).
3. Court projection — ball 2D → court coords via the validated auto-calibration
   homography → serve landing zones, rally map.
4. Fine-tune TrackNet on padel frames (semi-automated labeling) if 71% → higher
   is needed for reliable bounce/hit detection.
