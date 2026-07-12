import { useState, useEffect } from 'react'
import { supabase, PUB_R2 } from '../supabase'
import { isDemoAccount, DEMO_CTX } from '../demo'

const STATUS_BADGE = {
  recording:   { label: 'Recording',   cls: 'badge-queued' },
  uploaded:    { label: 'Uploaded',    cls: 'badge-queued' },
  queued:      { label: 'Queued',      cls: 'badge-queued' },
  processing:  { label: 'Processing',  cls: 'badge-processing' },
  done:        { label: 'Done',        cls: 'badge-done' },
  failed:      { label: 'Failed',      cls: '' },
}

function fmt(sec) {
  const m = Math.floor(sec / 60)
  return `${m} min`
}

function fmtDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function Matches({ session, player: playerProp, onSelect, onSignOut }) {
  const [player, setPlayer]   = useState(playerProp || null)
  const [rows, setRows]       = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      const email = session.user.email

      const p = playerProp || await supabase
        .from('padel_players')
        .select('id, name')
        .eq('email', email)
        .maybeSingle()
        .then(r => r.data)

      setPlayer(p)

      setPlayer(p)
      if (!p) { setLoading(false); return }

      const { data } = await supabase
        .from('padel_match_players')
        .select(`
          player_slot,
          heatmap_r2_key,
          padel_matches (
            id,
            started_at,
            status,
            duration_sec,
            padel_courts (
              name,
              padel_clubs ( name, city )
            ),
            padel_match_outputs (
              rally_count,
              highlight_r2_key
            )
          )
        `)
        .eq('player_id', p.id)
        .order('created_at', { ascending: false })

      setRows(data || [])
      setLoading(false)
    }
    load()
  }, [session])

  async function signOut() {
    if (onSignOut) { onSignOut(); return }
    await supabase.auth.signOut()
  }

  const email = session.user.email

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>

      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '20px 20px 16px',
        borderBottom: '1px solid var(--border)',
        position: 'sticky', top: 0, background: 'var(--bg)', zIndex: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <img src="/nsci-logo.png" alt="NSCI" style={{ width: 36, height: 36, flexShrink: 0 }} />
          <div>
            <div style={{ fontSize: '17px', fontWeight: '800', letterSpacing: '-0.5px', color: 'var(--text)' }}>
              PadelMind
            </div>
            <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '1px' }}>
              {player?.name || email}
            </div>
          </div>
        </div>
        <button
          onClick={signOut}
          style={{ background: 'none', border: 'none', color: 'var(--muted)', fontSize: '13px', cursor: 'pointer', padding: '6px 10px' }}
        >
          Sign out
        </button>
      </div>

      {/* Body */}
      <div style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>

        {loading && (
          <div style={{ color: 'var(--muted)', fontSize: '14px', textAlign: 'center', marginTop: '48px' }}>
            Loading matches…
          </div>
        )}

        {!loading && !player && (
          <div style={{ textAlign: 'center', marginTop: '48px' }}>
            <div style={{ fontSize: '36px', marginBottom: '12px' }}>👋</div>
            <p style={{ color: 'var(--muted)', fontSize: '14px' }}>
              Your profile isn't set up yet.<br />Ask your club admin to add you.
            </p>
          </div>
        )}

        {!loading && player && rows.length === 0 && !isDemoAccount(session.user.email) && (
          <div style={{ textAlign: 'center', marginTop: '48px' }}>
            <div style={{ fontSize: '36px', marginBottom: '12px' }}>📹</div>
            <p style={{ color: 'var(--muted)', fontSize: '14px' }}>
              No matches recorded yet.<br />Play and we'll handle the rest.
            </p>
          </div>
        )}

        {/* Persistent demo match — only for demo accounts */}
        {!loading && isDemoAccount(session.user.email) && (
          <div
            className="card"
            onClick={() => onSelect(DEMO_CTX)}
            style={{ cursor: 'pointer', transition: 'border-color 0.15s' }}
            onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--amber)')}
            onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
              <div>
                <div style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text)' }}>Court 2 · Demo Match</div>
                <div style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '3px' }}>NSCI Padel Club</div>
              </div>
              <span className="badge badge-done" style={{ flexShrink: 0 }}>Done</span>
            </div>
            <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
              <Stat label="Rallies" value={DEMO_CTX.rallyCount} />
              <Stat label="Duration" value={fmt(DEMO_CTX.durationSec)} />
              <Stat label="Distance" value={`${DEMO_CTX.demoExtra.zones.player_1.distance_km} km`} />
            </div>
            <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--hot)', fontWeight: '600' }}>
              Tap to view sample report →
            </div>
          </div>
        )}

        {rows.map(row => {
          const match  = row.padel_matches
          const court  = match?.padel_courts
          const club   = court?.padel_clubs
          const output = match?.padel_match_outputs?.[0]
          const badge  = STATUS_BADGE[match?.status] || { label: match?.status, cls: '' }
          const done   = match?.status === 'done'

          return (
            <div
              key={match?.id}
              className="card"
              onClick={() => done && onSelect({
                matchId:     match.id,
                playerSlot:  row.player_slot,
                heatmapKey:  row.heatmap_r2_key,
                highlightKey: output?.highlight_r2_key,
                rallyCount:  output?.rally_count,
                durationSec: match?.duration_sec,
              })}
              style={{
                cursor: done ? 'pointer' : 'default',
                opacity: match?.status === 'failed' ? 0.5 : 1,
                transition: 'border-color 0.15s',
              }}
              onMouseEnter={e => done && (e.currentTarget.style.borderColor = 'var(--amber)')}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <div>
                  <div style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text)' }}>
                    {fmtDate(match?.started_at)}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '3px' }}>
                    {court?.name}{club?.name ? ` · ${club.name}` : ''}
                  </div>
                </div>
                <span className={`badge ${badge.cls}`} style={{ flexShrink: 0 }}>
                  {badge.label}
                </span>
              </div>

              {done && output && (
                <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
                  <Stat label="Rallies" value={output.rally_count ?? '—'} />
                  {match.duration_sec && <Stat label="Duration" value={fmt(match.duration_sec)} />}
                  <Stat label="Slot" value={`P${row.player_slot}`} />
                </div>
              )}

              {done && (
                <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--amber)', fontWeight: '600' }}>
                  Tap to view →
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
      <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</span>
      <span style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text)' }}>{value}</span>
    </div>
  )
}
