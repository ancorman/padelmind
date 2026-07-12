import { useState } from 'react'
import { supabase } from '../supabase'

const AX_WABA = 'https://wa.me/918850291643?text=Hi%2C%20I%27ve%20registered%20on%20PadelMind%20and%20would%20like%20to%20receive%20match%20updates.'

export default function Register({ session, onRegistered }) {
  const email = session.user.email

  const [membershipNo, setMembershipNo] = useState('')
  const [name, setName]                 = useState('')
  const [phone, setPhone]               = useState('')
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState('')
  const [done, setDone]                 = useState(false)

  async function submit() {
    if (!membershipNo.trim()) { setError('Membership number is required.'); return }
    if (!name.trim())         { setError('Full name is required.'); return }
    if (phone.replace(/\D/g, '').length < 10) { setError('Enter a valid 10-digit WhatsApp number.'); return }
    setError(''); setLoading(true)

    const normalizedPhone = phone.startsWith('+') ? phone : `+91${phone.replace(/\D/g, '')}`

    const { error: e } = await supabase.from('padel_players').upsert({
      email: email.toLowerCase(),
      phone: normalizedPhone,
      name: name.trim(),
      membership_no: membershipNo.trim().toUpperCase(),
      status: 'pending',
    }, { onConflict: 'email' })

    setLoading(false)
    if (e) { setError(e.message); return }
    setDone(true)
  }

  if (done) {
    return (
      <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
        <h2 style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text)', marginBottom: '8px' }}>
          Request Submitted
        </h2>
        <p style={{ color: 'var(--muted)', fontSize: '14px', lineHeight: '1.6', marginBottom: '28px' }}>
          The club admin will verify your NSCI membership and approve your account — usually within 24 hours.
        </p>

        {/* WA opt-in nudge */}
        <div style={{ background: 'rgba(var(--green-rgb),0.08)', border: '1px solid rgba(var(--green-rgb),0.3)', borderRadius: '16px', padding: '20px', marginBottom: '24px', width: '100%', maxWidth: '360px' }}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>💬</div>
          <div style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text)', marginBottom: '6px' }}>
            Get match alerts on WhatsApp
          </div>
          <div style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '14px', lineHeight: '1.6' }}>
            Receive your heatmap, highlight reel and rally stats directly on WhatsApp after each match.
          </div>
          <a
            href={AX_WABA}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'block', background: 'var(--wa)', color: 'white',
              textDecoration: 'none', borderRadius: '10px',
              padding: '10px 20px', fontSize: '13px', fontWeight: '700',
            }}
          >
            Connect on WhatsApp →
          </a>
        </div>

        <button className="btn-ghost" onClick={onRegistered}>
          Continue to app
        </button>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '28px', maxWidth: '420px', margin: '0 auto', width: '100%' }}>

      <div style={{ textAlign: 'center', marginBottom: '36px' }}>
        <img src="/nsci-logo.png" alt="NSCI" style={{ width: 72, height: 72, display: 'block', margin: '0 auto 12px' }} />
        <h1 style={{ fontSize: '22px', fontWeight: '800', color: 'var(--text)', letterSpacing: '-0.5px' }}>
          Complete Registration
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: '13px', marginTop: '6px' }}>
          Your details are verified against the NSCI member list.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

        <div>
          <label style={labelStyle}>Email (from login)</label>
          <div style={{ background: 'var(--bg-elev)', border: '1.5px solid var(--border)', borderRadius: '12px', padding: '14px 16px', color: 'var(--muted)', fontSize: '14px' }}>
            {email}
          </div>
        </div>

        <div>
          <label style={labelStyle}>NSCI Membership Number</label>
          <input
            type="text"
            placeholder="e.g. OB7880"
            value={membershipNo}
            onChange={e => setMembershipNo(e.target.value)}
            autoFocus
            autoCapitalize="characters"
          />
        </div>

        <div>
          <label style={labelStyle}>Full Name</label>
          <input
            type="text"
            placeholder="As per NSCI membership"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </div>

        <div>
          <label style={labelStyle}>WhatsApp Number</label>
          <input
            type="tel"
            placeholder="+91 98200 00000"
            value={phone}
            onChange={e => setPhone(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && submit()}
          />
        </div>

        {error && <p style={{ color: 'var(--danger)', fontSize: '13px' }}>{error}</p>}

        <button
          className="btn-primary"
          onClick={submit}
          disabled={loading || !membershipNo.trim() || !name.trim() || phone.replace(/\D/g, '').length < 10}
        >
          {loading ? 'Submitting…' : 'Request Access'}
        </button>

        <p style={{ color: 'var(--muted)', fontSize: '11px', textAlign: 'center', lineHeight: '1.6' }}>
          Approval typically within 24 hours.
        </p>
      </div>
    </div>
  )
}

const labelStyle = {
  fontSize: '11px', color: 'var(--muted)', fontWeight: '700',
  display: 'block', marginBottom: '7px',
  textTransform: 'uppercase', letterSpacing: '0.5px',
}
