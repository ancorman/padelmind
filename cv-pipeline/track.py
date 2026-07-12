import numpy as np
import supervision as sv
from collections import defaultdict


def build_tracker() -> sv.ByteTrack:
    # minimum_matching_threshold lowered from 0.8: at 5 FPS sampling, players move
    # far between frames, so inter-frame IoU is low
    return sv.ByteTrack(minimum_matching_threshold=0.3)


def update(tracker: sv.ByteTrack, detections: list[dict]) -> list[dict]:
    """Feed detections into ByteTracker, return list with track_id added."""
    if not detections:
        return []

    xyxy   = np.array([d["bbox"] for d in detections], dtype=np.float32)
    confs  = np.array([d["conf"] for d in detections], dtype=np.float32)
    class_ids = np.zeros(len(detections), dtype=int)

    sv_dets = sv.Detections(xyxy=xyxy, confidence=confs, class_id=class_ids)
    tracked = tracker.update_with_detections(sv_dets)

    result = []
    for i, track_id in enumerate(tracked.tracker_id):
        x1, y1, x2, y2 = tracked.xyxy[i]
        result.append({
            "track_id": int(track_id),
            "bbox": [x1, y1, x2, y2],
            "foot": [(x1 + x2) / 2, y2],
        })
    return result


def assign_slots(
    track_history: dict[int, list[tuple[float, float]]],
    court_width: float = 10.0,
    court_length: float = 20.0,
) -> dict[int, int]:
    """
    Map track_id → slot (1-4) using average court position during warm-up.
    Near half (y < length/2): slots 1 & 2. Far half: slots 3 & 4.
    Left (x < width/2): odd slot. Right: even slot.
    """
    if not track_history:
        return {}

    avg_positions: dict[int, tuple[float, float]] = {}
    for track_id, pts in track_history.items():
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        avg_positions[track_id] = (np.mean(xs), np.mean(ys))

    # Sort into 4 quadrants
    half_y = court_length / 2
    half_x = court_width / 2

    near_left  = [(tid, pos) for tid, pos in avg_positions.items() if pos[1] <= half_y and pos[0] <= half_x]
    near_right = [(tid, pos) for tid, pos in avg_positions.items() if pos[1] <= half_y and pos[0] > half_x]
    far_left   = [(tid, pos) for tid, pos in avg_positions.items() if pos[1] > half_y  and pos[0] <= half_x]
    far_right  = [(tid, pos) for tid, pos in avg_positions.items() if pos[1] > half_y  and pos[0] > half_x]

    slot_map: dict[int, int] = {}
    for slot, group in [(1, near_left), (2, near_right), (3, far_left), (4, far_right)]:
        if group:
            # If multiple trackers in same quadrant (unusual), take the one with most data
            best = max(group, key=lambda x: len(track_history[x[0]]))
            slot_map[best[0]] = slot

    return slot_map
