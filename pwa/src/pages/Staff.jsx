import { useState, useEffect } from 'react'
import { supabase } from '../supabase'

const WABA = '918850291643' // AX WhatsApp Business number

function fmtTime(iso) {
  return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
}

function normalizePhone(raw) {
  const digits = raw.replace(/\D/g, '')
  if (raw.trim().startsWith('+')) return raw.trim().replace(/\s/g, '')
  if (digits.length === 10) return `+91${digits}`
  return `+${digits}`
}

function optInUrl(matchId) {
  return `https://wa.me/${WABA}?text=${encodeURIComponent(`PADEL OPTIN ${matchId}`)}`
}

export default function Staff({ session, player, activeBooking }) {
  const [activeMatch, setActiveMatch] = useState(null)
  const [loading, setLoading]         = useState(true)
  const [busy, setBusy]               = useState(false)
  const [error, setError]             = useState('')
  const [msg, setMsg]                 = useState('')
  const [phones, setPhones]           = useState(['', '', ''])  // P2, P3, P4 — kept after start for share section
  const [copied, setCopied]           = useState(false)

  useEffect(() => {
    if (!activeBooking) return
    fetchActiveMatch()
  }, [activeBooking])

  async function fetchActiveMatch() {
    setLoading(true)
    const { data } = await supabase
      .from('padel_matches')
      .select('id, started_at, status')
      .eq('court_id', activeBooking.court_id)
      .eq('status', 'recording')
      .order('started_at', { ascending: false })
      .limit(1)
      .maybeSingle()
    setActiveMatch(data)
    setLoading(false)
  }

  async function startMatch() {
    setBusy(true); setError(''); setMsg('')

    const allPhones = [player.phone, ...phones.filter(p => p.trim().length >= 10).map(normalizePhone)]
      .filter(Boolean)

    const { data: matchRows, error: me } = await supabase
      .from('padel_matches')
      .insert({ court_id: activeBooking.court_id, started_at: new Date().toISOString(), status: 'recording' })
      .select('id')
    if (me || !matchRows?.length) { setError(me?.message || 'Failed to start match.'); setBusy(false); return }
    const matchId = matchRows[0].id

    for (let i = 0; i < allPhones.length; i++) {
      const pp = allPhones[i]
      const { data: existing } = await supabase.from('padel_players').select('id').eq('phone', pp).maybeSingle()
      let playerId = existing?.id
      if (!playerId) {
        const { data: newP } = await supabase
          .from('padel_players')
          .insert({ phone: pp, status: 'pending' })
          .select('id')
        playerId = newP?.[0]?.id
      }
      await supabase.from('padel_match_players').insert({
        match_id: matchId,
        player_id: playerId || null,
        player_phone: pp,
        player_slot: i + 1,
      })
    }

    setBusy(false)
    setMsg('')
    // keep phones in state so the share section can use them
    await fetchActiveMatch()
  }

  async function endMatch() {
    if (!activeMatch) return
    setBusy(true); setError(''); setMsg('')
    const { error: ue } = await supabase
      .from('padel_matches')
      .update({ status: 'uploaded', ended_at: new Date().toISOString() })
      .eq('id', activeMatch.id)
    setBusy(false)
    if (ue) { setError(ue.message); return }
    setMsg('Match ended. Your heatmap + highlight reel will arrive on WhatsApp within 15 minutes.')
    setActiveMatch(null)
    setPhones(['', '', ''])
  }

  async function shareWithTeam() {
    const url  = optInUrl(activeMatch.id)
    const text = `We're recording our padel match at NSCI 🎾\n\nTap this link to opt in and receive your heatmap + highlight reel on WhatsApp within 15 min of match end:\n\n${url}`
    if (navigator.share) {
      navigator.share({ text }).catch(() => {})
    } else {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    }
  }

  if (!activeBooking) return null

  const { court_name, sessionStart, sessionEnd } = activeBooking
  const enteredPhones = phones.filter(p => p.trim().length >= 10)

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>

      {/* Header */}
      <div style={{ padding: '20px 20px 14px', borderBottom: '1px solid var(--border)', background: 'var(--bg)', position: 'sticky', top: 0, zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <img src="/nsci-logo.png" alt="" style={{ width: 30, height: 30 }} />
          <div>
            <div style={{ fontSize: '16px', fontWeight: '800', color: 'var(--text)' }}>My Match</div>
            <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
              {court_name} · {fmtTime(sessionStart)} – {fmtTime(sessionEnd)}
            </div>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

        {msg && (
          <div style={{ background: 'rgba(var(--green-rgb),0.1)', border: '1px solid rgba(var(--green-rgb),0.35)', borderRadius: '10px', padding: '14px', fontSize: '13px', color: 'var(--green)', lineHeight: '1.6' }}>
            {msg}
          </div>
        )}
        {error && (
          <div style={{ background: 'rgba(var(--danger-rgb),0.1)', border: '1px solid var(--danger)', borderRadius: '10px', padding: '12px 14px', fontSize: '13px', color: 'var(--danger)' }}>
            {error}
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--muted)', fontSize: '13px' }}>Checking court status…</div>
        ) : activeMatch ? (
          /* ── Active match ── */
          <div className="card" style={{ borderColor: 'rgba(var(--danger-rgb),0.5)' }}>

            {/* Recording indicator */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--danger)', flexShrink: 0, animation: 'pulse 1.5s infinite' }} />
              <div>
                <div style={{ fontSize: '14px', fontWeight: '800', color: 'var(--text)' }}>Recording in progress</div>
                <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>Started at {fmtTime(activeMatch.started_at)}</div>
              </div>
            </div>

            <div style={{ background: 'var(--bg)', borderRadius: '8px', padding: '10px 12px', fontSize: '11px', color: 'var(--muted)', marginBottom: '16px' }}>
              Match ID: <span style={{ color: 'var(--text)', fontWeight: '700' }}>{activeMatch.id.slice(0, 8)}…</span>
            </div>

            {/* ── Opt-in section ── */}
            <div style={{ background: 'rgba(var(--amber-rgb),0.07)', border: '1px solid rgba(var(--amber-rgb),0.25)', borderRadius: '10px', padding: '14px', marginBottom: '14px' }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--amber)', marginBottom: '4px' }}>📲 Get your highlight reel on WhatsApp</div>
              <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '12px', lineHeight: '1.6' }}>
                Tap below to confirm your WhatsApp number. Your heatmap + reel will be sent there within 15 minutes of match end.
              </div>

              {/* P1 opt-in */}
              <a
                href={optInUrl(activeMatch.id)}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'block', textAlign: 'center', padding: '13px 16px',
                  background: 'var(--wa)', borderRadius: '10px', color: '#fff',
                  fontWeight: '700', fontSize: '14px', textDecoration: 'none',
                  marginBottom: enteredPhones.length ? '10px' : 0,
                }}
              >
                ✅ Opt in — receive my reel
              </a>

              {/* Share with teammates */}
              {enteredPhones.length > 0 && (
                <>
                  <div style={{ fontSize: '10px', color: 'var(--muted)', textAlign: 'center', marginBottom: '8px' }}>
                    Send the same link to your teammates so they get theirs too
                  </div>
                  <button
                    onClick={shareWithTeam}
                    style={{
                      width: '100%', padding: '12px 16px',
                      background: 'rgba(var(--wa-rgb),0.12)', border: '1.5px solid rgba(var(--wa-rgb),0.4)',
                      borderRadius: '10px', color: 'var(--wa)',
                      fontWeight: '700', fontSize: '13px', cursor: 'pointer',
                    }}
                  >
                    {copied ? '✅ Copied!' : '🔗 Share opt-in link with teammates'}
                  </button>
                </>
              )}
            </div>

            <button
              className="btn-primary"
              onClick={endMatch}
              disabled={busy}
              style={{ background: 'var(--danger)' }}
            >
              {busy ? 'Ending…' : 'End Match — Stop Recording'}
            </button>
          </div>

        ) : (
          /* ── No active match — show Start form ── */
          <div className="card">
            <div style={{ fontSize: '14px', fontWeight: '800', color: 'var(--text)', marginBottom: '4px' }}>{court_name}</div>
            <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '18px' }}>
              Ready to record · {fmtTime(sessionStart)} – {fmtTime(sessionEnd)}
            </div>

            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>Players</div>

              {/* P1 — pre-filled */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', color: 'var(--amber)', width: '18px', textAlign: 'right', flexShrink: 0, fontWeight: '700' }}>P1</span>
                <div style={{ flex: 1, background: 'var(--bg-elev)', border: '1.5px solid var(--amber)', borderRadius: '12px', padding: '14px 16px', fontSize: '14px', color: 'var(--muted)' }}>
                  {player?.phone || 'You'} <span style={{ fontSize: '11px', marginLeft: '6px' }}>(you)</span>
                </div>
              </div>

              {phones.map((ph, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--muted)', width: '18px', textAlign: 'right', flexShrink: 0 }}>P{i + 2}</span>
                  <input
                    type="tel"
                    placeholder="+91 XXXXX XXXXX (optional)"
                    value={ph}
                    onChange={e => setPhones(prev => prev.map((v, j) => j === i ? e.target.value : v))}
                    style={{ flex: 1 }}
                  />
                </div>
              ))}
            </div>

            <button
              className="btn-primary"
              onClick={startMatch}
              disabled={busy || !player?.phone}
            >
              {busy ? 'Starting…' : 'Start Match — Begin Recording'}
            </button>
          </div>
        )}

        <div style={{ background: 'rgba(var(--hot-rgb),0.06)', border: '1px solid rgba(var(--hot-rgb),0.2)', borderRadius: '10px', padding: '12px 14px' }}>
          <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--amber)', marginBottom: '6px' }}>How it works</div>
          <div style={{ fontSize: '11px', color: 'var(--muted)', lineHeight: '1.7' }}>
            Tap <strong style={{ color: 'var(--text)' }}>Start Match</strong> when you step on court — the camera begins recording.<br/>
            Tap <strong style={{ color: 'var(--text)' }}>Opt in on WhatsApp</strong> to confirm your number for delivery.<br/>
            Tap <strong style={{ color: 'var(--text)' }}>End Match</strong> when you finish — heatmap + reel arrive on WhatsApp within 15 minutes.
          </div>
        </div>

      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  )
}
