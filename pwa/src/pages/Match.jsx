import { useState } from 'react'
import { PUB_R2 } from '../supabase'

function r2url(key) {
  if (!key) return null
  return `${PUB_R2}/${key}`
}

function fmtSec(sec) {
  if (!sec) return '—'
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return s > 0 ? `${m}m ${s}s` : `${m} min`
}

export default function Match({ ctx, onBack }) {
  const { matchId, playerSlot, heatmapKey, highlightKey, rallyCount, durationSec } = ctx
  const [videoErr, setVideoErr] = useState(false)
  const [imgErr, setImgErr]     = useState(false)

  const heatmapUrl  = r2url(heatmapKey)
  const highlightUrl = r2url(highlightKey)

  const avgRallyDuration = rallyCount && durationSec
    ? Math.round(durationSec / rallyCount)
    : null

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>

      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        padding: '16px 20px',
        borderBottom: '1px solid var(--border)',
        position: 'sticky', top: 0, background: 'var(--bg)', zIndex: 10,
      }}>
        <button
          onClick={onBack}
          style={{ background: 'none', border: 'none', color: 'var(--amber)', fontSize: '20px', cursor: 'pointer', padding: '0 4px', lineHeight: 1 }}
        >
          ←
        </button>
        <div>
          <div style={{ fontSize: '17px', fontWeight: '800', color: 'var(--text)', letterSpacing: '-0.3px' }}>
            Match Detail
          </div>
          <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '1px' }}>
            Player {playerSlot}
          </div>
        </div>
      </div>

      <div style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

        {/* Stats strip */}
        <div className="card" style={{ display: 'flex', justifyContent: 'space-around' }}>
          <StatBlock label="Rallies" value={rallyCount ?? '—'} />
          <div style={{ width: '1px', background: 'var(--border)' }} />
          <StatBlock label="Duration" value={fmtSec(durationSec)} />
          <div style={{ width: '1px', background: 'var(--border)' }} />
          <StatBlock label="Avg Rally" value={avgRallyDuration ? `${avgRallyDuration}s` : '—'} />
        </div>

        {/* Heatmap */}
        {heatmapUrl && !imgErr ? (
          <div>
            <SectionLabel>Your Movement Heatmap</SectionLabel>
            <div style={{ borderRadius: '16px', overflow: 'hidden', border: '1px solid var(--border)' }}>
              <img
                src={heatmapUrl}
                alt="Player heatmap"
                onError={() => setImgErr(true)}
                style={{ width: '100%', display: 'block' }}
              />
            </div>
          </div>
        ) : heatmapUrl && imgErr ? (
          <div className="card" style={{ color: 'var(--muted)', fontSize: '13px', textAlign: 'center' }}>
            Heatmap unavailable
          </div>
        ) : (
          <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>📍</div>
            <p style={{ color: 'var(--muted)', fontSize: '13px' }}>
              Heatmap will appear after court calibration
            </p>
          </div>
        )}

        {/* Highlight reel */}
        {highlightUrl && !videoErr ? (
          <div>
            <SectionLabel>Highlight Reel</SectionLabel>
            <div style={{ borderRadius: '16px', overflow: 'hidden', border: '1px solid var(--border)', background: '#000' }}>
              <video
                src={highlightUrl}
                controls
                playsInline
                onError={() => setVideoErr(true)}
                style={{ width: '100%', display: 'block', maxHeight: '60vh' }}
              />
            </div>
          </div>
        ) : highlightUrl && videoErr ? (
          <div className="card" style={{ color: 'var(--muted)', fontSize: '13px', textAlign: 'center' }}>
            Video unavailable
          </div>
        ) : (
          <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>🎬</div>
            <p style={{ color: 'var(--muted)', fontSize: '13px' }}>
              Highlight reel processing
            </p>
          </div>
        )}

      </div>
    </div>
  )
}

function StatBlock({ label, value }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', padding: '4px 8px' }}>
      <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</span>
      <span style={{ fontSize: '22px', fontWeight: '800', color: 'var(--amber)', letterSpacing: '-0.5px' }}>{value}</span>
    </div>
  )
}

function SectionLabel({ children }) {
  return (
    <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '10px' }}>
      {children}
    </div>
  )
}
