import { useState, useEffect } from 'react'
import { supabase } from '../supabase'

const REDIRECT = window.location.origin

export default function Login() {
  const [email, setEmail]     = useState('')
  const [sent, setSent]       = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  // Poll for session every 3s after link is sent.
  // If the user clicks the magic link on another device/tab, the session
  // lands in localStorage there — but this tab won't auto-detect it via
  // onAuthStateChange. Polling getSession() catches it within 3s.
  useEffect(() => {
    if (!sent) return
    const timer = setInterval(async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (session) clearInterval(timer) // App.jsx onAuthStateChange takes over
    }, 3000)
    return () => clearInterval(timer)
  }, [sent])

  async function sendLink() {
    setError(''); setLoading(true)
    const { error: e } = await supabase.auth.signInWithOtp({
      email: email.trim().toLowerCase(),
      options: { emailRedirectTo: REDIRECT },
    })
    setLoading(false)
    if (e) { setError(e.message); return }
    setSent(true)
  }

  if (sent) {
    return (
      <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px', textAlign: 'center' }}>
        <div style={{ fontSize: '52px', marginBottom: '16px' }}>📧</div>
        <h2 style={{ fontSize: '22px', fontWeight: '800', color: 'var(--text)', marginBottom: '10px' }}>
          Check your email
        </h2>
        <p style={{ color: 'var(--muted)', fontSize: '14px', lineHeight: '1.7', marginBottom: '8px' }}>
          We sent a sign-in link to
        </p>
        <p style={{ color: 'var(--amber)', fontWeight: '700', fontSize: '15px', marginBottom: '24px' }}>
          {email}
        </p>
        <div style={{
          background: 'var(--bg-elev)', border: '1px solid var(--border)',
          borderRadius: '14px', padding: '16px 20px', marginBottom: '28px',
          fontSize: '13px', color: 'var(--muted)', lineHeight: '1.8', textAlign: 'left',
          maxWidth: '320px',
        }}>
          <div style={{ marginBottom: '8px' }}>
            1. Open the email on <strong style={{ color: 'var(--text)' }}>this device</strong>
          </div>
          <div style={{ marginBottom: '8px' }}>
            2. Tap <strong style={{ color: 'var(--amber)' }}>Sign in</strong> — the link opens the app
          </div>
          <div>
            3. This screen updates automatically ✓
          </div>
        </div>
        <p style={{ color: 'var(--muted)', fontSize: '12px', marginBottom: '24px' }}>
          Link expires in 15 minutes.
        </p>
        <button className="btn-ghost" onClick={() => { setSent(false); setEmail('') }}>
          Use a different email
        </button>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '32px 24px' }}>

      <div style={{ textAlign: 'center', marginBottom: '48px' }}>
        <img src="/nsci-logo.png" alt="NSCI" style={{ width: 90, height: 90, display: 'block', margin: '0 auto 12px' }} />
        <h1 style={{ fontSize: '30px', fontWeight: '800', color: 'var(--text)', letterSpacing: '-0.5px', marginBottom: '4px' }}>
          PadelMind
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: '12px', marginBottom: '6px', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
          NSCI Padel Club
        </p>
        <p style={{ color: 'var(--muted)', fontSize: '13px' }}>
          Your match. Your data. Your edge.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <label style={labelStyle}>Email Address</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && email.length >= 5 && sendLink()}
            autoFocus
            autoComplete="email"
          />
        </div>

        {error && <p style={{ color: 'var(--danger)', fontSize: '13px' }}>{error}</p>}

        <button
          className="btn-primary"
          onClick={sendLink}
          disabled={loading || email.length < 5}
          style={{ marginTop: '4px' }}
        >
          {loading ? 'Sending…' : 'Send Sign-in Link'}
        </button>

        <p style={{ color: 'var(--muted)', fontSize: '12px', textAlign: 'center', lineHeight: '1.6' }}>
          A sign-in link will be emailed to you.<br />No password needed.
        </p>
      </div>
    </div>
  )
}

const labelStyle = {
  fontSize: '12px', color: 'var(--muted)', fontWeight: '700',
  display: 'block', marginBottom: '8px',
  textTransform: 'uppercase', letterSpacing: '0.5px',
}
