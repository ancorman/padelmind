import { useState, useEffect } from 'react'
import { supabase } from './supabase'
import Login from './pages/Login'
import Register from './pages/Register'
import Matches from './pages/Matches'
import Match from './pages/Match'
import Book from './pages/Book'
import Staff from './pages/Staff'
import { isDemo, DEMO_CTX } from './demo'

// ── Top-level states ──────────────────────────────────────────────────────────
// loading → auth check
// unauth  → Login
// register → Register (phone verified but no player record)
// pending  → awaiting admin approval
// app      → main experience (tab: matches | book)

export default function App() {
  const [appState, setAppState] = useState('loading')
  const [session, setSession]   = useState(null)
  const [player, setPlayer]     = useState(null)
  const [tab, setTab]           = useState('matches')   // matches | book | staff
  const [matchCtx, setMatchCtx] = useState(null)
  const [activeBooking, setActiveBooking] = useState(null) // {court_id, court_name, sessionStart, sessionEnd}

  // ── Auth listener ─────────────────────────────────────────────────────────
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session: s } }) => {
      setSession(s)
      if (s) resolvePlayer(s)
      else setAppState('unauth')
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, s) => {
      setSession(s)
      if (s) resolvePlayer(s)
      else setAppState('unauth')
    })
    return () => subscription.unsubscribe()
  }, [])

  async function resolvePlayer(s) {
    const { data: p } = await supabase
      .from('padel_players')
      .select('id, name, email, phone, status')
      .eq('email', s.user.email)
      .maybeSingle()

    setPlayer(p)
    if (!p)                          setAppState('register')
    else if (p.status === 'pending') setAppState('pending')
    else {
      setAppState('app')
      const ab = await checkActiveBooking(p.id)
      setActiveBooking(ab)
    }
  }

  async function checkActiveBooking(playerId) {
    const now = new Date()
    const today = new Date(); today.setHours(0, 0, 0, 0)
    const tomorrow = new Date(today); tomorrow.setDate(tomorrow.getDate() + 1)

    const { data: bookings } = await supabase
      .from('padel_bookings')
      .select('slot_time, court_id, padel_courts(name)')
      .eq('player_id', playerId)
      .eq('status', 'confirmed')
      .gte('slot_time', today.toISOString())
      .lt('slot_time', tomorrow.toISOString())
      .order('slot_time')

    if (!bookings?.length) return null

    const SLOT_MS = 30 * 60 * 1000
    const BUFFER_BEFORE = 10 * 60 * 1000  // show tab 10 min before first slot
    const BUFFER_AFTER  = 30 * 60 * 1000  // keep tab 30 min after last slot ends

    // Group by court
    const byCourt = {}
    for (const b of bookings) {
      if (!byCourt[b.court_id]) byCourt[b.court_id] = []
      byCourt[b.court_id].push(b)
    }

    for (const courtBookings of Object.values(byCourt)) {
      courtBookings.sort((a, b) => new Date(a.slot_time) - new Date(b.slot_time))
      const firstSlot = new Date(courtBookings[0].slot_time)
      const lastSlot  = new Date(courtBookings[courtBookings.length - 1].slot_time)
      const windowStart = new Date(firstSlot.getTime() - BUFFER_BEFORE)
      const windowEnd   = new Date(lastSlot.getTime() + SLOT_MS + BUFFER_AFTER)

      if (now >= windowStart && now <= windowEnd) {
        return {
          court_id:     courtBookings[0].court_id,
          court_name:   courtBookings[0].padel_courts?.name,
          sessionStart: firstSlot,
          sessionEnd:   new Date(lastSlot.getTime() + SLOT_MS),
        }
      }
    }
    return null
  }

  function handleRegistered() {
    setAppState('pending')
  }

  // Re-check active booking every 60 seconds so the tab auto-appears/disappears
  useEffect(() => {
    if (appState !== 'app' || !player) return
    const timer = setInterval(async () => {
      const ab = await checkActiveBooking(player.id)
      setActiveBooking(ab)
      if (!ab && tab === 'staff') setTab('matches')
    }, 60_000)
    return () => clearInterval(timer)
  }, [appState, player])

  async function signOut() {
    await supabase.auth.signOut()
    setPlayer(null)
    setTab('matches')
    setMatchCtx(null)
    setActiveBooking(null)
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  // Demo mode (?demo) — render the populated report with faux data, no auth/DB
  if (isDemo()) return <Match ctx={DEMO_CTX} onBack={() => { window.location.search = '' }} />

  if (appState === 'loading') return <Centered>Loading…</Centered>

  if (appState === 'unauth')  return <Login />

  if (appState === 'register') return <Register session={session} onRegistered={handleRegistered} />

  if (appState === 'pending') return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px', textAlign: 'center' }}>
      <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
      <h2 style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text)', marginBottom: '10px' }}>
        Awaiting Approval
      </h2>
      <p style={{ color: 'var(--muted)', fontSize: '14px', lineHeight: '1.6', marginBottom: '32px' }}>
        Your registration is pending club admin approval.<br />
        You'll be notified once you're verified.
      </p>
      <button className="btn-ghost" onClick={signOut}>Sign out</button>
    </div>
  )

  // ── Main app ───────────────────────────────────────────────────────────────
  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', paddingBottom: '64px' }}>

      {/* Page content */}
      <div style={{ flex: 1 }}>
        {tab === 'matches' && !matchCtx && (
          <Matches
            session={session}
            player={player}
            onSelect={ctx => setMatchCtx(ctx)}
            onSignOut={signOut}
          />
        )}
        {tab === 'matches' && matchCtx && (
          <Match ctx={matchCtx} onBack={() => setMatchCtx(null)} />
        )}
        {tab === 'book' && (
          <Book session={session} player={player} onBack={() => setTab('matches')} />
        )}
        {tab === 'staff' && (
          <Staff session={session} player={player} activeBooking={activeBooking} />
        )}
      </div>

      {/* Bottom nav */}
      <div style={{
        position: 'fixed', bottom: 0, left: 0, right: 0,
        background: 'var(--bg-elev)', borderTop: '1px solid var(--border)',
        display: 'flex', zIndex: 40,
      }}>
        <NavTab
          label="My Matches"
          icon="📹"
          active={tab === 'matches'}
          onClick={() => { setTab('matches'); setMatchCtx(null) }}
        />
        <NavTab
          label="Book Court"
          icon="🎾"
          active={tab === 'book'}
          onClick={() => setTab('book')}
        />
        {activeBooking && (
          <NavTab
            label="My Match"
            icon="🎬"
            active={tab === 'staff'}
            onClick={() => setTab('staff')}
          />
        )}
      </div>
    </div>
  )
}

function NavTab({ label, icon, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1, background: 'none', border: 'none', cursor: 'pointer',
        padding: '10px 8px 14px',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px',
        color: active ? 'var(--amber)' : 'var(--muted)',
        transition: 'color 0.15s',
      }}
    >
      <span style={{ fontSize: '20px' }}>{icon}</span>
      <span style={{ fontSize: '10px', fontWeight: active ? '700' : '500', letterSpacing: '0.3px' }}>{label}</span>
    </button>
  )
}

function Centered({ children }) {
  return (
    <div style={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontSize: '14px' }}>
      {children}
    </div>
  )
}
