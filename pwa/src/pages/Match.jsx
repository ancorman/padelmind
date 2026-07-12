import { useState, useEffect } from 'react'
import { supabase, PUB_R2 } from '../supabase'

// Intensity accent (echoes the heatmap fire colours) — per UI_MATCH_REPORT_SCOPE.
const HOT = '#FB923C'

function r2url(key) {
  return key ? `${PUB_R2}/${key}` : null
}

function fmtSec(sec) {
  if (!sec) return '—'
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return s > 0 ? `${m}m ${s}s` : `${m} min`
}

function fmtDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

export default function Match({ ctx, onBack }) {
  const { matchId, playerSlot, heatmapKey, highlightKey, rallyCount, durationSec } = ctx
  const [videoErr, setVideoErr] = useState(false)
  const [imgErr, setImgErr]     = useState(false)
  const [extra, setExtra]       = useState(null)   // { zones, rallyWindows, courtName, startedAt }
  const [loaded, setLoaded]     = useState(false)

  useEffect(() => {
    let alive = true
    async function load() {
      const { data } = await supabase
        .from('padel_matches')
        .select(`
          started_at,
          padel_courts ( name ),
          padel_match_outputs ( zones_summary, rally_windows )
        `)
        .eq('id', matchId)
        .maybeSingle()
      if (!alive) return
      const out = data?.padel_match_outputs?.[0]
      setExtra({
        zones: out?.zones_summary || null,
        rallyWindows: out?.rally_windows || [],
        courtName: data?.padel_courts?.name || 'Match',
        startedAt: data?.started_at || null,
      })
      setLoaded(true)
    }
    load()
    return () => { alive = false }
  }, [matchId])

  const heatmapUrl  = r2url(heatmapKey)
  const highlightUrl = r2url(highlightKey)

  // The player's own stats block out of zones_summary { player_1: {...}, ... }
  const me = extra?.zones?.[`player_${playerSlot}`] || null
  const longestRally = extra?.zones?.longest_rally_sec
    ?? (extra?.rallyWindows?.length
        ? Math.max(...extra.rallyWindows.map(w => w.duration_sec || 0))
        : null)

  const avgRally = rallyCount && durationSec ? Math.round(durationSec / rallyCount) : null
  const courtName = extra?.courtName || 'Match'

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>

      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        padding: '16px 20px', borderBottom: '1px solid var(--border)',
        position: 'sticky', top: 0, background: 'var(--bg)', zIndex: 10,
      }}>
        <button onClick={onBack}
          style={{ background: 'none', border: 'none', color: 'var(--amber)', fontSize: '20px', cursor: 'pointer', padding: '0 4px', lineHeight: 1 }}>
          ←
        </button>
        <div>
          <div style={{ fontSize: '17px', fontWeight: '800', color: 'var(--text)', letterSpacing: '-0.3px' }}>
            {courtName}{extra?.startedAt ? ` · ${fmtDate(extra.startedAt)}` : ''}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '1px' }}>
            Your match report · Player {playerSlot}
          </div>
        </div>
      </div>

      <div style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

        {/* Hero stat strip */}
        <div className="card" style={{ display: 'flex', justifyContent: 'space-around' }}>
          <StatBlock label="Rallies" value={rallyCount ?? '—'} />
          <Divider />
          <StatBlock label="Duration" value={fmtSec(durationSec)} />
          <Divider />
          <StatBlock label="Distance" value={me?.distance_km != null ? `${me.distance_km} km` : '—'} accent={HOT} />
        </div>

        {/* Movement — only when stats exist */}
        {me && (
          <div>
            <SectionLabel>Your Movement</SectionLabel>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <Tile icon="🏃" label="Distance run" value={`${me.distance_km} km`} accent={HOT} />
              <Tile icon="⚡" label="Top speed" value={me.top_speed_kmh ? `${me.top_speed_kmh} km/h` : '—'} accent={HOT} />
              <Tile icon="💨" label="Sprints" value={me.sprint_count ?? '—'} />
              <Tile icon="📊" label="Avg speed" value={me.avg_speed_kmh ? `${me.avg_speed_kmh} km/h` : '—'} />
            </div>
          </div>
        )}

        {/* Court positioning */}
        {me?.zones && (
          <div>
            <SectionLabel>Court Positioning</SectionLabel>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <SplitBar leftLabel="Net" leftPct={me.zones.net_pct}
                        rightLabel="Baseline" rightPct={me.zones.baseline_pct} />
              <SplitBar leftLabel="Left side" leftPct={me.zones.left_pct}
                        rightLabel="Right side" rightPct={me.zones.right_pct} />
            </div>
          </div>
        )}

        {/* Intensity fade note */}
        {me?.fade_min != null && (
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '10px', borderColor: 'rgba(251,146,60,0.35)' }}>
            <span style={{ fontSize: '20px' }}>📉</span>
            <span style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.5 }}>
              Your intensity dipped after <strong style={{ color: HOT }}>minute {me.fade_min}</strong> — worth pacing for next time.
            </span>
          </div>
        )}

        {/* Longest rally callout */}
        {longestRally ? (
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '20px' }}>🔥</span>
            <span style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.5 }}>
              Longest rally: <strong style={{ color: HOT }}>{Math.round(longestRally)} sec</strong>
              {avgRally ? <> · avg rally {avgRally}s</> : null} — it's in your highlights.
            </span>
          </div>
        ) : null}

        {/* Heatmap */}
        {heatmapUrl && !imgErr ? (
          <div>
            <SectionLabel>Your Movement Heatmap</SectionLabel>
            <div style={{ borderRadius: '16px', overflow: 'hidden', border: '1px solid var(--border)' }}>
              <img src={heatmapUrl} alt="Player heatmap" onError={() => setImgErr(true)}
                   style={{ width: '100%', display: 'block' }} />
            </div>
          </div>
        ) : heatmapUrl && imgErr ? (
          <EmptyCard icon="📍" text="Heatmap unavailable" />
        ) : (
          <EmptyCard icon="📍" text="Heatmap will appear after court calibration" />
        )}

        {/* Highlight reel */}
        {highlightUrl && !videoErr ? (
          <div>
            <SectionLabel>Highlight Reel</SectionLabel>
            <div style={{ borderRadius: '16px', overflow: 'hidden', border: '1px solid var(--border)', background: '#000' }}>
              <video src={highlightUrl} controls playsInline onError={() => setVideoErr(true)}
                     style={{ width: '100%', display: 'block', maxHeight: '60vh' }} />
            </div>
          </div>
        ) : highlightUrl && videoErr ? (
          <EmptyCard icon="🎬" text="Video unavailable" />
        ) : (
          <EmptyCard icon="🎬" text="Highlight reel processing" />
        )}

        {/* Coming soon — Tier P, no dates (PHASE_FEATURE_MAP governance) */}
        <div>
          <SectionLabel>Coming Soon</SectionLabel>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <ComingTile icon="🎾" label="Ball & shot tracking" />
            <ComingTile icon="🤸" label="Technique analysis" />
          </div>
        </div>

        {!loaded && (
          <div style={{ textAlign: 'center', color: 'var(--muted)', fontSize: '12px' }}>
            Loading your stats…
          </div>
        )}

      </div>
    </div>
  )
}

/* ── local components ─────────────────────────────────────────────── */

function StatBlock({ label, value, accent }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', padding: '4px 8px' }}>
      <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</span>
      <span style={{ fontSize: '22px', fontWeight: '800', color: accent || 'var(--amber)', letterSpacing: '-0.5px' }}>{value}</span>
    </div>
  )
}

function Divider() {
  return <div style={{ width: '1px', background: 'var(--border)' }} />
}

function SectionLabel({ children }) {
  return (
    <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '10px' }}>
      {children}
    </div>
  )
}

function Tile({ icon, label, value, accent }) {
  return (
    <div className="card" style={{ padding: '14px' }}>
      <div style={{ fontSize: '18px', marginBottom: '6px' }}>{icon}</div>
      <div style={{ fontSize: '20px', fontWeight: '800', color: accent || 'var(--text)', letterSpacing: '-0.5px' }}>{value}</div>
      <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>{label}</div>
    </div>
  )
}

function SplitBar({ leftLabel, leftPct, rightLabel, rightPct }) {
  const l = Math.max(0, Math.min(100, leftPct ?? 0))
  const r = Math.max(0, Math.min(100, rightPct ?? 0))
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--muted)', marginBottom: '5px' }}>
        <span><strong style={{ color: 'var(--text)' }}>{l}%</strong> {leftLabel}</span>
        <span>{rightLabel} <strong style={{ color: 'var(--text)' }}>{r}%</strong></span>
      </div>
      <div style={{ display: 'flex', height: '8px', borderRadius: '6px', overflow: 'hidden', background: 'var(--bg)' }}>
        <div style={{ width: `${l}%`, background: HOT }} />
        <div style={{ width: `${r}%`, background: 'var(--amber)' }} />
      </div>
    </div>
  )
}

function EmptyCard({ icon, text }) {
  return (
    <div className="card" style={{ textAlign: 'center' }}>
      <div style={{ fontSize: '24px', marginBottom: '8px' }}>{icon}</div>
      <p style={{ color: 'var(--muted)', fontSize: '13px' }}>{text}</p>
    </div>
  )
}

function ComingTile({ icon, label }) {
  return (
    <div className="card" style={{ padding: '14px', opacity: 0.6, display: 'flex', alignItems: 'center', gap: '10px' }}>
      <span style={{ fontSize: '18px' }}>{icon}</span>
      <span style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: 600 }}>{label}</span>
    </div>
  )
}
