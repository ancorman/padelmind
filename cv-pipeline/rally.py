from dataclasses import dataclass
import numpy as np


@dataclass
class RallyWindow:
    start_sec: float
    end_sec: float

    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec

    def to_dict(self) -> dict:
        return {
            "start_sec": round(self.start_sec, 2),
            "end_sec": round(self.end_sec, 2),
            "duration_sec": round(self.duration_sec, 2),
        }


def detect(
    position_log: list[dict],
    min_duration: float = 3.0,
    speed_threshold: float = 0.4,
    window_sec: float = 1.0,
    gap_merge_sec: float = 2.0,
) -> list[RallyWindow]:
    """
    position_log: [{timestamp, slot, court_x, court_y}]
    Returns list of RallyWindow sorted by start_sec.

    Rally heuristic:
    - Bin positions into 1-second windows
    - Compute average player speed per window (metres/sec)
    - Window is "active" if avg speed across all players > speed_threshold
    - Rally = consecutive active windows lasting >= min_duration
    """
    if not position_log:
        return []

    # Group by 1-second bins
    bins: dict[int, list[dict]] = {}
    for entry in position_log:
        bin_idx = int(entry["timestamp"])
        bins.setdefault(bin_idx, []).append(entry)

    # For each bin, estimate activity via position variance across players
    # (velocity needs consecutive positions per player — use spread as proxy)
    sorted_bins = sorted(bins.keys())

    active_times: list[float] = []
    for b in sorted_bins:
        entries = bins[b]
        if len(entries) < 2:
            continue
        # Average pairwise distance between players (court coverage)
        pts = [(e["court_x"], e["court_y"]) for e in entries]
        spread = np.std([p[0] for p in pts]) + np.std([p[1] for p in pts])
        if spread > speed_threshold:
            active_times.append(float(b))

    if not active_times:
        return []

    # Merge consecutive active seconds into windows
    windows: list[RallyWindow] = []
    start = active_times[0]
    prev  = active_times[0]

    for t in active_times[1:]:
        if t - prev <= gap_merge_sec:
            prev = t
        else:
            windows.append(RallyWindow(start, prev + window_sec))
            start = t
            prev  = t
    windows.append(RallyWindow(start, prev + window_sec))

    # Filter by minimum duration
    return [w for w in windows if w.duration_sec >= min_duration]
