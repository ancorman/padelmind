"""Synthetic-data tests for the Phase 1.5 stats layer. Run:
   .venv/bin/python -m pytest test_stats.py -q   (or plain python test_stats.py)
"""

import stats


def _walk(speed_ms, duration_s, fps=5, y=5.0):
    """Player pacing along x at constant speed, bouncing between walls."""
    samples, x, direction = [], 1.0, 1
    step = speed_ms / fps
    for i in range(int(duration_s * fps)):
        samples.append((i / fps, x, y))
        x += step * direction
        if x >= 9.0 or x <= 1.0:
            direction *= -1
    return samples


def test_distance_constant_speed():
    # 2 m/s for 100 s = 200 m
    s = stats.player_stats(_walk(2.0, 100), 100)
    assert abs(s["distance_km"] - 0.20) < 0.01, s["distance_km"]
    assert abs(s["avg_speed_kmh"] - 7.2) < 0.5, s["avg_speed_kmh"]


def test_stationary_player():
    samples = [(i / 5, 5.0, 5.0) for i in range(500)]
    s = stats.player_stats(samples, 100)
    assert s["distance_km"] == 0.0
    assert s["sprint_count"] == 0
    assert s["top_speed_kmh"] == 0.0


def test_tracker_jump_despiked():
    # one 15 m teleport (tracker glitch) must not count as distance
    samples = [(0.0, 1.0, 5.0), (0.2, 1.1, 5.0), (0.4, 16.0 - 14.9, 19.0), (0.6, 1.2, 5.0)]
    # jump of ~14m in 0.2s = 70 m/s → despiked
    s = stats.player_stats([(t, x, y) for t, x, y in samples], 1)
    assert s["distance_km"] < 0.001


def test_sprint_detection():
    # 30 s walk, 3 s burst at 4.5 m/s, 30 s walk → exactly 1 sprint
    fps = 5
    samples, t, x = [], 0.0, 1.0
    for phase_speed, phase_dur in [(1.0, 30), (4.5, 3), (1.0, 30)]:
        step, direction = phase_speed / fps, 1
        for _ in range(int(phase_dur * fps)):
            samples.append((t, x, 5.0))
            t += 1 / fps
            x += step * direction
            if x >= 9.0 or x <= 1.0:
                direction *= -1
    s = stats.player_stats(samples, t)
    assert s["sprint_count"] == 1, s["sprint_count"]


def test_net_vs_baseline_zones():
    at_net = [(i / 5, 5.0, 9.0) for i in range(100)]        # 1 m from net
    s = stats.player_stats(at_net, 20)
    assert s["zones"]["net_pct"] == 100.0
    assert s["zones"]["baseline_pct"] == 0.0

    at_back = [(i / 5, 5.0, 1.0) for i in range(100)]       # 9 m from net
    s = stats.player_stats(at_back, 20)
    assert s["zones"]["net_pct"] == 0.0
    assert s["zones"]["baseline_pct"] == 100.0


def test_compute_shapes_callback_payload():
    log = []
    for i in range(300):
        t = i / 5
        log.append({"timestamp": t, "slot": 1, "court_x": 3.0 + (i % 10) * 0.1, "court_y": 5.0})
        log.append({"timestamp": t, "slot": 3, "court_x": 7.0, "court_y": 15.0})
        log.append({"timestamp": t, "slot": 0, "court_x": 5.0, "court_y": 10.0})  # unassigned → skipped
    rallies = [{"duration_sec": 12.5}, {"duration_sec": 31.0}, {"duration_sec": 8.0}]
    out = stats.compute(log, rallies, 60)
    assert "player_1" in out and "player_3" in out and "player_2" not in out
    assert out["longest_rally_sec"] == 31.0
    assert out["player_1"]["zones"]["net_pct"] is not None


if __name__ == "__main__":
    import sys
    mod = sys.modules[__name__]
    fails = 0
    for name in dir(mod):
        if name.startswith("test_"):
            try:
                getattr(mod, name)()
                print(f"  PASS  {name}")
            except AssertionError as e:
                print(f"  FAIL  {name}: {e}")
                fails += 1
    sys.exit(1 if fails else 0)
