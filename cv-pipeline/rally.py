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
    position_log: [{timestamp, slot, court_x, court_y}]  (slots 1,2 = near half;
    3,4 = far half). Returns RallyWindows sorted by start_sec.

    Rally heuristic (per SOW — velocity based, and BOTH-SIDES active):
    - Per player (by slot), court-metre speed between consecutive samples.
    - A 1-second window is "active" only when BOTH sides of the net show a moving
      player (max speed on each half > speed_threshold). This is the rally signal:
      a live exchange has both teams reacting; one player walking to fetch a ball,
      or one team repositioning between points, does NOT light up both halves.
    - Rally = consecutive active seconds (gaps <= gap_merge_sec bridged), kept if
      >= min_duration.
    NOTE: speed_threshold still needs tuning on real footage — see tune_rally.py,
    which fits it against a handful of hand-marked rallies.
    """
    if not position_log:
        return []

    HALF = {1: "near", 2: "near", 3: "far", 4: "far"}
    by_slot: dict[int, list[dict]] = {}
    for e in position_log:
        if e.get("slot", 0) in (1, 2, 3, 4):
            by_slot.setdefault(e["slot"], []).append(e)

    # per 1-second bin → {'near': [speeds], 'far': [speeds]}
    bins: dict[int, dict[str, list[float]]] = {}
    for slot, entries in by_slot.items():
        entries.sort(key=lambda e: e["timestamp"])
        half = HALF[slot]
        for a, b in zip(entries, entries[1:]):
            dt = b["timestamp"] - a["timestamp"]
            if dt <= 0 or dt > 2.0:          # skip tracking gaps
                continue
            dist = ((b["court_x"] - a["court_x"]) ** 2 + (b["court_y"] - a["court_y"]) ** 2) ** 0.5
            speed = dist / dt
            if speed > 12.0:                  # despike tracker jumps (>12 m/s isn't a human)
                continue
            bins.setdefault(int(b["timestamp"]), {}).setdefault(half, []).append(speed)

    active_times: list[float] = []
    for b in sorted(bins):
        near = max(bins[b].get("near", [0.0]))
        far = max(bins[b].get("far", [0.0]))
        if near > speed_threshold and far > speed_threshold:   # BOTH sides moving
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
