import { useState, useEffect, useRef } from 'react'
import { supabase } from '../supabase'

const MEMBER_PRICE = 400
const GUEST_PRICE  = 1000   // NSCI official guest rate
const PRICE = MEMBER_PRICE

// Booking window: 10:00 AM to 11:30 PM (configurable; mirrors NSCI Hudle settings)
const BOOK_START_HOUR = 6    // 6:00 AM
const BOOK_END_HOUR   = 23   // last slot starts at 23:30

function makeSlots() {
  const out = []
  for (let h = BOOK_START_HOUR; h <= BOOK_END_HOUR; h++) {
    for (let m = 0; m < 60; m += 30) {
      const hh = String(h).padStart(2, '0')
      const mm = String(m).padStart(2, '0')
      const disp = h === 0 ? 12 : h > 12 ? h - 12 : h
      const ampm = h < 12 ? 'AM' : 'PM'
      out.push({
        key: `${hh}:${mm}`,
        label: `${String(disp).padStart(2, '0')}:${mm} ${ampm}`,
        hour: h, min: m,
        icon: h >= 6 && h < 18 ? '☀️' : '🌙',
      })
    }
  }
  return out
}
const SLOTS = makeSlots()

function today0() {
  const d = new Date(); d.setHours(0, 0, 0, 0); return d
}
function addDays(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x }
function fmtHeader(d) {
  return d.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
}
function slotIso(date, h, m) {
  const d = new Date(date); d.setHours(h, m, 0, 0); return d.toISOString()
}

export default function Book({ session, player: playerProp, onBack }) {
  const [stage, setStage]       = useState('slots')  // slots | summary | done
  const [club, setClub]         = useState(null)
  const [courts, setCourts]     = useState([])
  const [player, setPlayer]     = useState(null)
  const [date, setDate]         = useState(today0())
  const [booked, setBooked]     = useState([])        // [{court_id, slot_time, player_id}]
  const [bookedToday, setBookedToday] = useState(0)  // player's confirmed slots today
  const [sel, setSel]           = useState([])        // [{courtId, courtName, key, iso, label}]
  const [loading, setLoading]   = useState(true)
  const [confirming, setConf]   = useState(false)
  const [error, setError]       = useState('')
  const [guestSlots, setGuest]  = useState({})  // key → true if guest booking
  const gridRef = useRef(null)

  function totalAmount() {
    return sel.reduce((sum, s) => sum + (guestSlots[s.key + s.courtId] ? GUEST_PRICE : MEMBER_PRICE), 0)
  }

  useEffect(() => {
    async function init() {
      const [{ data: p }, { data: cl }] = await Promise.all([
        playerProp
          ? Promise.resolve({ data: playerProp })
          : supabase.from('padel_players').select('id,name').eq('email', session.user.email).maybeSingle(),
        supabase.from('padel_clubs').select('id,name,city').eq('active', true).limit(1).maybeSingle(),
      ])
      setPlayer(p)
      setClub(cl)
      if (cl) {
        const { data: ct } = await supabase
          .from('padel_courts').select('id,name').eq('club_id', cl.id).eq('active', true).order('name')
        setCourts(ct || [])
      }
      setLoading(false)
    }
    init()
  }, [session])

  useEffect(() => {
    if (!courts.length) return
    fetchBooked()
  }, [date, courts, player])

  // Auto-scroll to first available (non-past) slot when grid loads
  useEffect(() => {
    if (loading || stage !== 'slots') return
    const now = new Date()
    const firstAvailable = SLOTS.find(s => {
      const d = new Date(date); d.setHours(s.hour, s.min, 0, 0)
      return d >= now
    })
    if (!firstAvailable && date <= today0()) {
      // All today's slots are past — jump to tomorrow
      setDate(addDays(today0(), 1))
      return
    }
    if (firstAvailable && gridRef.current) {
      const idx = SLOTS.indexOf(firstAvailable)
      const rowH = 48
      gridRef.current.scrollTop = Math.max(0, idx * rowH - 80)
    }
  }, [loading, courts, date])

  async function fetchBooked() {
    const start = new Date(date)
    const end   = addDays(date, 1)
    const [{ data: allBooked }, { count }] = await Promise.all([
      supabase
        .from('padel_bookings')
        .select('court_id,slot_time,player_id')
        .in('court_id', courts.map(c => c.id))
        .gte('slot_time', start.toISOString())
        .lt('slot_time', end.toISOString())
        .eq('status', 'confirmed'),
      // Separate count: player's OWN confirmed slots today (any court, any club)
      player?.id
        ? supabase
            .from('padel_bookings')
            .select('*', { count: 'exact', head: true })
            .eq('player_id', player.id)
            .gte('slot_time', start.toISOString())
            .lt('slot_time', end.toISOString())
            .eq('status', 'confirmed')
        : Promise.resolve({ count: 0 }),
    ])
    setBooked(allBooked || [])
    setBookedToday(count ?? 0)
  }

  function isBooked(courtId, s) {
    const ts = new Date(slotIso(date, s.hour, s.min)).getTime()
    return booked.some(b => b.court_id === courtId && new Date(b.slot_time).getTime() === ts)
  }
  function isPast(s) {
    // Only grey out slots on dates strictly before today, not today's past slots.
    // This lets admins enter bookings for the full current day during the pilot.
    const today = today0()
    const slotDate = new Date(date); slotDate.setHours(0, 0, 0, 0)
    return slotDate < today
  }
  function isSel(courtId, key) { return sel.some(x => x.courtId === courtId && x.key === key) }

  function toggle(court, s) {
    if (isBooked(court.id, s) || isPast(s)) return
    const iso = slotIso(date, s.hour, s.min)
    if (isSel(court.id, s.key)) {
      setSel(p => p.filter(x => !(x.courtId === court.id && x.key === s.key)))
    } else {
      // 90-min daily cap = 3 slots max (confirmed bookings today + newly selected in this session)
      if (sel.length + bookedToday >= 3) {
        setError('NSCI limit: max 90 minutes (3 slots) per day.')
        return
      }
      setError('')
      setSel(p => [...p, { courtId: court.id, courtName: court.name, key: s.key, iso, label: s.label, date: fmtHeader(date) }])
    }
  }

  async function confirm() {
    if (!player || !sel.length) return
    setConf(true); setError('')
    const { error: e } = await supabase.from('padel_bookings').insert(
      sel.map(s => {
        const isGuest = !!guestSlots[s.key + s.courtId]
        return { court_id: s.courtId, player_id: player.id, slot_time: s.iso, amount: isGuest ? GUEST_PRICE : MEMBER_PRICE, is_guest: isGuest }
      })
    )
    setConf(false)
    if (e) { setError(e.message); return }
    setSel([])
    await fetchBooked()
    setStage('done')
  }

  if (loading) return (
    <div style={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontSize: '14px' }}>
      Loading courts…
    </div>
  )

  if (stage === 'done') return <ConfirmScreen onBack={onBack} />

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>

      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '12px', padding: '14px 20px',
        borderBottom: '1px solid var(--border)', background: 'var(--bg)',
        position: 'sticky', top: 0, zIndex: 20,
      }}>
        <button onClick={stage === 'summary' ? () => setStage('slots') : onBack}
          style={{ background: 'none', border: 'none', color: 'var(--amber)', fontSize: '20px', cursor: 'pointer', padding: '0 4px', lineHeight: 1 }}>
          ←
        </button>
        <img src="/nsci-logo.png" alt="NSCI" style={{ width: 30, height: 30, flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '15px', fontWeight: '800', color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {club?.name || 'Book a Court'}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
            {stage === 'slots' ? fmtHeader(date) : 'Booking Summary'}
          </div>
        </div>
      </div>

      {stage === 'slots' && (
        <>
          {/* Date nav */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '10px 20px', borderBottom: '1px solid var(--border)',
            background: 'var(--bg)', position: 'sticky', top: '57px', zIndex: 19,
          }}>
            <button onClick={() => setDate(d => addDays(d, -1))}
              disabled={date <= today0()}
              style={{ background: 'none', border: 'none', color: date <= today0() ? 'var(--border)' : 'var(--amber)', fontSize: '14px', fontWeight: '700', cursor: date <= today0() ? 'default' : 'pointer' }}>
              ‹ Prev
            </button>
            <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text)' }}>{fmtHeader(date)}</span>
            <button onClick={() => setDate(d => addDays(d, 1))}
              style={{ background: 'none', border: 'none', color: 'var(--amber)', fontSize: '14px', fontWeight: '700', cursor: 'pointer' }}>
              Next ›
            </button>
          </div>

          {/* Legend */}
          <div style={{
            display: 'flex', gap: '12px', padding: '8px 12px',
            borderBottom: '1px solid var(--border)', background: 'var(--bg)',
            position: 'sticky', top: '100px', zIndex: 19, flexWrap: 'wrap',
          }}>
            {[
              { color: 'rgba(var(--hot-rgb),0.18)', label: 'Available', text: 'var(--amber)' },
              { color: 'var(--amber)', label: 'Selected', text: 'var(--bg)' },
              { color: 'rgba(var(--border-rgb),0.5)', label: 'Booked', text: 'var(--muted)' },
              { color: 'rgba(var(--border-rgb),0.18)', label: 'Past', text: 'var(--border)' },
            ].map(l => (
              <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <div style={{ width: '14px', height: '14px', borderRadius: '4px', background: l.color, flexShrink: 0 }} />
                <span style={{ fontSize: '10px', color: 'var(--muted)' }}>{l.label}</span>
              </div>
            ))}
          </div>

          {/* Court column headers */}
          <div style={{
            display: 'grid', gridTemplateColumns: `56px repeat(${courts.length}, 1fr)`,
            padding: '0 8px', borderBottom: '1px solid var(--border)',
            background: 'var(--bg)', position: 'sticky', top: '141px', zIndex: 18,
          }}>
            <div />
            {courts.map(c => (
              <div key={c.id} style={{ textAlign: 'center', padding: '8px 4px', fontSize: '12px', fontWeight: '700', color: 'var(--text)' }}>
                {c.name}
              </div>
            ))}
          </div>

          {/* 90-min cap warning */}
          {error && (
            <div style={{ background: 'rgba(var(--danger-rgb),0.12)', border: '1px solid var(--danger)', borderRadius: '10px', margin: '8px 8px 0', padding: '10px 14px', fontSize: '12px', color: 'var(--danger)', fontWeight: '600' }}>
              ⚠️ {error}
            </div>
          )}

          {/* Slot grid */}
          <div ref={gridRef} style={{ flex: 1, overflowY: 'auto', padding: '0 8px 120px' }}>
            {SLOTS.map(s => (
              <div key={s.key} style={{
                display: 'grid', gridTemplateColumns: `56px repeat(${courts.length}, 1fr)`,
                alignItems: 'center', minHeight: '48px',
                borderBottom: '1px solid rgba(var(--border-rgb),0.4)',
              }}>
                {/* Time label */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1px' }}>
                  <span style={{ fontSize: '9px' }}>{s.icon}</span>
                  <span style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: '600' }}>{s.label}</span>
                </div>

                {/* Court cells */}
                {courts.map(c => {
                  const booked_ = isBooked(c.id, s)
                  const past_   = isPast(s)
                  const sel_    = isSel(c.id, s.key)

                  const bg = sel_    ? 'var(--amber)'
                           : booked_ ? 'rgba(var(--border-rgb),0.4)'
                           : past_   ? 'rgba(var(--border-rgb),0.2)'
                           : 'rgba(var(--hot-rgb),0.12)'

                  const color = sel_ ? 'white'
                              : booked_ || past_ ? 'var(--muted)'
                              : 'var(--amber)'

                  return (
                    <div key={c.id}
                      onClick={() => toggle(c, s)}
                      style={{
                        margin: '3px 4px',
                        borderRadius: '8px',
                        background: bg,
                        color,
                        fontSize: '11px',
                        fontWeight: '700',
                        textAlign: 'center',
                        padding: '8px 4px',
                        cursor: booked_ || past_ ? 'default' : 'pointer',
                        minHeight: '36px',
                        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        userSelect: 'none',
                        transition: 'background 0.1s',
                        border: sel_ ? '1.5px solid var(--amber)' : 'none',
                      }}
                    >
                      {booked_ ? <span style={{ fontSize: '10px' }}>Booked</span>
                       : past_  ? <span style={{ fontSize: '9px' }}>—</span>
                       : sel_   ? <><span style={{ fontSize: '13px' }}>✓</span><span style={{ fontSize: '10px' }}>₹{PRICE}</span></>
                       : <><span style={{ fontSize: '10px', fontWeight: '800' }}>Open</span><span style={{ fontSize: '10px', opacity: 0.8 }}>₹{PRICE}</span></>
                      }
                    </div>
                  )
                })}
              </div>
            ))}
          </div>

          {/* Bottom selection bar — sits above the 64px nav bar */}
          {sel.length > 0 && (
            <div style={{
              position: 'fixed', bottom: '64px', left: 0, right: 0,
              background: 'var(--amber)', padding: '14px 20px',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              zIndex: 50,
              boxShadow: '0 -2px 12px rgba(0,0,0,0.3)',
            }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: '800', color: 'white' }}>
                  {sel.length} Slot{sel.length > 1 ? 's' : ''} Selected
                </div>
                <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.75)' }}>
                  ₹{sel.length * PRICE} total
                </div>
              </div>
              <button
                onClick={() => setStage('summary')}
                style={{ background: 'white', color: 'var(--amber)', border: 'none', borderRadius: '10px', padding: '10px 22px', fontWeight: '800', fontSize: '13px', cursor: 'pointer' }}>
                PROCEED →
              </button>
            </div>
          )}
        </>
      )}

      {stage === 'summary' && (
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px 40px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* T&C card */}
          <div style={{ background: 'rgba(var(--green-rgb),0.08)', border: '1px solid rgba(var(--green-rgb),0.3)', borderRadius: '12px', padding: '14px' }}>
            <div style={{ fontSize: '12px', fontWeight: '800', color: 'var(--green)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Terms & Conditions
            </div>
            {[
              '90 minutes per day, 180 minutes per week (Mon–Sun cycle).',
              'Bookings are non-cancellable. No slot transfers.',
              'Member must be present during booking with physical or digital membership card.',
              '1 guest allowed per session — guest charge ₹1,000.',
              'Unauthorised event bookings will not be valid.',
            ].map((t, i) => (
              <div key={i} style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '4px', display: 'flex', gap: '6px' }}>
                <span>•</span><span>{t}</span>
              </div>
            ))}
          </div>

          {/* Slots section */}
          <div className="card">
            <div style={{ fontSize: '11px', fontWeight: '800', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
              {sel.length} New Slot{sel.length > 1 ? 's' : ''}
            </div>
            {sel.map((s, i) => {
              const gkey = s.key + s.courtId
              const isGuest = !!guestSlots[gkey]
              const price = isGuest ? GUEST_PRICE : MEMBER_PRICE
              return (
                <div key={i} style={{ padding: '12px 0', borderBottom: i < sel.length - 1 ? '1px solid var(--border)' : 'none' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: '700', color: 'var(--amber)' }}>{s.courtName}</div>
                      <div style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '2px' }}>{s.date} · {s.label}</div>
                    </div>
                    <div style={{ fontSize: '15px', fontWeight: '800', color: isGuest ? 'var(--danger)' : 'var(--text)' }}>₹{price}</div>
                  </div>
                  {/* Guest toggle */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px', background: 'rgba(var(--border-rgb),0.3)', borderRadius: '10px', padding: '8px 12px' }}>
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text)' }}>Bringing a guest?</div>
                      <div style={{ fontSize: '11px', color: 'var(--muted)' }}>NSCI guest charge: ₹{GUEST_PRICE}/session</div>
                    </div>
                    <button
                      onClick={() => setGuest(g => ({ ...g, [gkey]: !g[gkey] }))}
                      style={{
                        background: isGuest ? 'var(--amber)' : 'var(--border)',
                        border: 'none', borderRadius: '20px',
                        width: '40px', height: '22px',
                        cursor: 'pointer', transition: 'background 0.2s',
                        position: 'relative', flexShrink: 0,
                      }}
                    >
                      <div style={{
                        position: 'absolute', top: '3px',
                        left: isGuest ? '20px' : '3px',
                        width: '16px', height: '16px',
                        background: 'white', borderRadius: '50%',
                        transition: 'left 0.2s',
                      }} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Booking user */}
          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Booking Member</div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text)', marginTop: '4px' }}>{player?.name || session.user.phone}</div>
            </div>
            <span style={{ fontSize: '20px' }}>👤</span>
          </div>

          {/* Payable */}
          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '13px', color: 'var(--muted)' }}>Payable to Membership Account</div>
              {sel.some(s => guestSlots[s.key + s.courtId]) && (
                <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>Includes guest surcharge</div>
              )}
            </div>
            <div style={{ fontSize: '22px', fontWeight: '800', color: 'var(--amber)' }}>₹{totalAmount()}</div>
          </div>

          {error && <div style={{ color: 'var(--danger)', fontSize: '13px', textAlign: 'center' }}>{error}</div>}

          <button className="btn-primary" onClick={confirm} disabled={confirming}>
            {confirming ? 'Confirming…' : 'Confirm Booking'}
          </button>
        </div>
      )}
    </div>
  )
}

function ConfirmScreen({ onBack }) {
  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px', textAlign: 'center' }}>
      <div style={{ fontSize: '56px', marginBottom: '20px' }}>✅</div>
      <h2 style={{ fontSize: '22px', fontWeight: '800', color: 'var(--text)', marginBottom: '10px' }}>Booking Confirmed!</h2>
      <p style={{ color: 'var(--muted)', fontSize: '14px', lineHeight: '1.6', marginBottom: '32px' }}>
        Your slot is locked in.<br />See you on the court.
      </p>
      <button className="btn-primary" onClick={onBack}>Done</button>
    </div>
  )
}
