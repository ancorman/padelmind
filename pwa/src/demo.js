// Demo mode — open the PWA with ?demo to see a fully-populated match report
// with faux data (no auth, no DB, no video). For showing the UI feel.
// Toggle: any URL with ?demo in the query string.

export const isDemo = () =>
  typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('demo')

// Faux player stats shaped exactly like the real zones_summary payload the CV
// pipeline writes to padel_match_outputs.zones_summary.
const DEMO_ZONES = {
  player_1: {
    distance_km: 3.4,
    top_speed_kmh: 18.6,
    avg_speed_kmh: 6.1,
    sprint_count: 12,
    fade_min: 45,
    zones: { left_pct: 58, right_pct: 42, net_pct: 27, baseline_pct: 54 },
    sample_count: 1840,
  },
  longest_rally_sec: 31,
}

// ctx shaped like what Matches.jsx passes into <Match>, plus demoExtra so the
// report skips its Supabase fetch.
export const DEMO_CTX = {
  matchId: 'demo-match',
  playerSlot: 1,
  heatmapKey: '__demo__',           // sentinel — Match maps this to /demo-heatmap.png
  highlightKey: null,               // no clip (as requested)
  rallyCount: 14,
  durationSec: 72 * 60,
  demoExtra: {
    zones: DEMO_ZONES,
    rallyWindows: [
      { start_sec: 320, end_sec: 351, duration_sec: 31 },
      { start_sec: 880, end_sec: 902, duration_sec: 22 },
      { start_sec: 1510, end_sec: 1528, duration_sec: 18 },
    ],
    courtName: 'Court 2',
    startedAt: new Date().toISOString(),
  },
}

export const DEMO_HEATMAP_URL = '/demo-heatmap.png'
