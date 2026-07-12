"""
Phase 1.5 stats layer — movement/tactics metrics from the positions log.

Pure computation on what Phase 1 already produces; no new CV. Output feeds the
WA V1.5 report template and the PWA match report page (see UI_MATCH_REPORT_SCOPE.md,
PHASE_FEATURE_MAP.md Tier S+).

Court frame: 10 m wide (x), 20 m long (y), net at y = 10.
Positions are sampled at ~5 FPS; gaps happen (occlusion, missed detection).
"""

from collections import defaultdict

NET_Y = 10.0
COURT_W = 10.0

MAX_SPEED_MS = 8.0        # despike cap — humans on court don't exceed this; tracker jumps do
SPRINT_SPEED_MS = 3.0     # burst threshold
SPRINT_MIN_SEC = 1.0      # burst must be sustained this long
NET_ZONE_M = 3.0          # within 3 m of the net = "at net"
BASELINE_ZONE_M = 7.0     # ≥7 m from net (within 3 m of back wall) = "baseline"
FADE_BUCKET_SEC = 300     # 5-minute intensity buckets
MAX_GAP_SEC = 2.0         # don't accumulate distance across longer tracking gaps


def _speeds(samples):
    """Per-interval (t, speed_m_s, dist_m) between consecutive samples, despiked."""
    out = []
    for (t0, x0, y0), (t1, x1, y1) in zip(samples, samples[1:]):
        dt = t1 - t0
        if dt <= 0 or dt > MAX_GAP_SEC:
            continue
        dist = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        speed = dist / dt
        if speed > MAX_SPEED_MS:      # tracker jump, not human movement
            continue
        out.append((t1, speed, dist))
    return out


def _sprints(intervals):
    """Count bursts of speed > SPRINT_SPEED_MS sustained ≥ SPRINT_MIN_SEC."""
    count = 0
    burst_start = None
    last_t = None
    for t, speed, _ in intervals:
        if speed >= SPRINT_SPEED_MS:
            if burst_start is None:
                burst_start = last_t if last_t is not None else t
        else:
            if burst_start is not None and (last_t - burst_start) >= SPRINT_MIN_SEC:
                count += 1
            burst_start = None
        last_t = t
    if burst_start is not None and last_t is not None and (last_t - burst_start) >= SPRINT_MIN_SEC:
        count += 1
    return count


def _fade_minute(intervals, duration_sec):
    """First 5-min bucket (after the peak) whose avg speed drops below 70% of peak.
    Returns the bucket's start minute, or None if intensity holds."""
    if duration_sec < 2 * FADE_BUCKET_SEC:
        return None                    # too short to talk about fade
    buckets = defaultdict(list)
    for t, speed, _ in intervals:
        buckets[int(t // FADE_BUCKET_SEC)].append(speed)
    if len(buckets) < 2:
        return None
    avgs = {b: sum(v) / len(v) for b, v in buckets.items() if v}
    peak_bucket = max(avgs, key=avgs.get)
    peak = avgs[peak_bucket]
    if peak <= 0:
        return None
    for b in sorted(avgs):
        if b > peak_bucket and avgs[b] < 0.7 * peak:
            return b * FADE_BUCKET_SEC // 60
    return None


def player_stats(samples, duration_sec):
    """
    samples: [(timestamp, court_x, court_y)] for ONE player, time-ordered.
    Returns the per-player stats dict (all Tier S+ metrics).
    """
    if len(samples) < 2:
        return None

    intervals = _speeds(samples)
    total_dist = sum(d for _, _, d in intervals)
    speeds = [s for _, s, _ in intervals]

    n = len(samples)
    near_net = sum(1 for _, _, y in samples if abs(y - NET_Y) <= NET_ZONE_M)
    baseline = sum(1 for _, _, y in samples if abs(y - NET_Y) >= BASELINE_ZONE_M)

    # Zone quadrants within the player's own half (majority half wins)
    own_near = sum(1 for _, _, y in samples if y <= NET_Y) >= n / 2
    half = [(x, y) for _, x, y in samples if (y <= NET_Y) == own_near]
    zl = sum(1 for x, _ in half if x <= COURT_W / 2)
    zones = {
        "left_pct": round(100 * zl / max(len(half), 1), 1),
        "right_pct": round(100 * (len(half) - zl) / max(len(half), 1), 1),
        "net_pct": round(100 * near_net / n, 1),
        "baseline_pct": round(100 * baseline / n, 1),
    }

    top_speed = max(speeds) if speeds else 0.0
    avg_speed = (sum(speeds) / len(speeds)) if speeds else 0.0

    return {
        "distance_km": round(total_dist / 1000, 2),
        "top_speed_kmh": round(top_speed * 3.6, 1),
        "avg_speed_kmh": round(avg_speed * 3.6, 1),
        "sprint_count": _sprints(intervals),
        "fade_min": _fade_minute(intervals, duration_sec),
        "zones": zones,
        "sample_count": n,
    }


def compute(position_log, rallies, duration_sec):
    """
    position_log: [{timestamp, slot, court_x, court_y}, ...] (slot 0 = unassigned, skipped)
    rallies: rally objects with .duration (or dicts with duration_sec) — longest is reported
    Returns {"player_1": {...}, ..., "longest_rally_sec": float} — shaped for the
    Worker callback `zones` field (stored as padel_match_outputs.zones_summary).
    """
    by_slot = defaultdict(list)
    for e in position_log:
        slot = e.get("slot", 0)
        if slot in (1, 2, 3, 4):
            by_slot[slot].append((e["timestamp"], e["court_x"], e["court_y"]))

    out = {}
    for slot in (1, 2, 3, 4):
        samples = sorted(by_slot.get(slot, []))
        stats = player_stats(samples, duration_sec)
        if stats:
            out[f"player_{slot}"] = stats

    longest = 0.0
    for r in rallies:
        d = getattr(r, "duration", None)
        if d is None and isinstance(r, dict):
            d = r.get("duration_sec", r.get("duration", 0))
        longest = max(longest, float(d or 0))
    out["longest_rally_sec"] = round(longest, 1)
    return out
