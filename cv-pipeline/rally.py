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
    speed_threshold: float = 0.5,
    window_sec: float = 1.0,
    gap_merge_sec: float = 2.0,
) -> list[RallyWindow]:
    """
    position_log: [{timestamp, slot, court_x, court_y}]
    Returns list of RallyWindow sorted by start_sec.

    Rally heuristic (per SOW — velocity based, NOT positional spread):
    - Per player (by slot), compute court-metre speed between consecutive samples
    - Bin into 1-second windows; a window is "active" if the mean player speed
      in it exceeds speed_threshold (m/s)
    - Rally = consecutive active seconds (gaps <= gap_merge_sec bridged),
      kept only if >= min_duration
    NOTE: speed_threshold needs tuning on real pilot footage — this is the first
    honest default, calibrate against a watched match (2-3 passes).
    """
    if not position_log:
        return []

    # Per-slot ordered samples → per-interval speed, tagged to its 1-second bin
    by_slot: dict[int, list[dict]] = {}
    for e in position_log:
        if e.get("slot", 0) in (1, 2, 3, 4):
            by_slot.setdefault(e["slot"], []).append(e)

    bin_speeds: dict[int, list[float]] = {}
    for slot, entries in by_slot.items():
        entries.sort(key=lambda e: e["timestamp"])
        for a, b in zip(entries, entries[1:]):
            dt = b["timestamp"] - a["timestamp"]
            if dt <= 0 or dt > 2.0:          # skip tracking gaps
                continue
            dist = ((b["court_x"] - a["court_x"]) ** 2 + (b["court_y"] - a["court_y"]) ** 2) ** 0.5
            speed = dist / dt
            if speed > 12.0:                  # despike tracker jumps (>12 m/s isn't a human)
                continue
            bin_speeds.setdefault(int(b["timestamp"]), []).append(speed)

    active_times: list[float] = []
    for b in sorted(bin_speeds):
        speeds = bin_speeds[b]
        if speeds and (sum(speeds) / len(speeds)) > speed_threshold:
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
