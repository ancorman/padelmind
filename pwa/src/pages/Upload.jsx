import { useState, useEffect } from 'react'
import { supabase } from '../supabase'

const WORKER = 'https://padelmind-api.manoj-5ce.workers.dev'
const WABA = '918850291643'

function normalizePhone(raw) {
  const digits = raw.replace(/\D/g, '')
  if (raw.trim().startsWith('+')) return raw.trim().replace(/\s/g, '')
  if (digits.length === 10) return `+91${digits}`
  return `+${digits}`
}

// Read a video file's duration (seconds) client-side
function videoDuration(file) {
  return new Promise((resolve) => {
    const v = document.createElement('video')
    v.preload = 'metadata'
    v.onloadedmetadata = () => { URL.revokeObjectURL(v.src); resolve(Math.round(v.duration) || 0) }
    v.onerror = () => resolve(0)
    v.src = URL.createObjectURL(file)
  })
}

// PUT the file to the presigned URL with progress
function putWithProgress(url, file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', url)
    xhr.setRequestHeader('Content-Type', file.type || 'video/mp4')
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress(e.loaded / e.total) }
    xhr.onload = () => (xhr.status >= 200 && xhr.status < 300) ? resolve() : reject(new Error(`Upload failed (${xhr.status})`))
    xhr.onerror = () => reject(new Error('Network error during upload'))
    xhr.send(file)
  })
}

export default function Upload({ player }) {
  const [courts, setCourts]   = useState([])
  const [courtId, setCourtId] = useState('')
  const [partners, setPartners] = useState(['', '', ''])
  const [file, setFile]       = useState(null)
  const [stage, setStage]     = useState('form')   // form | uploading | done
  const [pct, setPct]         = useState(0)
  const [step, setStep]       = useState('')
  const [error, setError]     = useState('')
  const [matchId, setMatchId] = useState(null)

  useEffect(() => {
    supabase.from('padel_courts').select('id, name').order('name').then(({ data }) => {
      setCourts(data || [])
      if (data?.length) setCourtId(data[0].id)
    })
  }, [])

  async function start() {
    setError('')
    if (!file) return setError('Pick your match video first.')
    if (!courtId) return setError('Choose the court you played on.')
    setStage('uploading'); setPct(0)

    try {
      // 1 — create the match
      setStep('Creating match…')
      const duration = await videoDuration(file)
      const now = new Date()
      const { data: mRows, error: me } = await supabase.from('padel_matches')
        .insert({ court_id: courtId, status: 'uploaded',
                  started_at: new Date(now - (duration || 0) * 1000).toISOString(),
                  ended_at: now.toISOString(), duration_sec: duration || null })
        .select('id')
      if (me || !mRows?.length) throw new Error(me?.message || 'Could not create match')
      const id = mRows[0].id
      setMatchId(id)

      // 2 — players (uploader = slot 1, partners after)
      const phones = [player.phone, ...partners.filter(p => p.trim().length >= 10).map(normalizePhone)]
      for (let i = 0; i < phones.length && i < 4; i++) {
        const pp = phones[i]
        const { data: ex } = await supabase.from('padel_players').select('id').eq('phone', pp).maybeSingle()
        let pid = ex?.id
        if (!pid) {
          const { data: np } = await supabase.from('padel_players').insert({ phone: pp, status: 'pending' }).select('id')
          pid = np?.[0]?.id
        }
        await supabase.from('padel_match_players').insert({ match_id: id, player_id: pid || null, player_phone: pp, player_slot: i + 1 })
      }

      // 3 — presigned upload URL
      setStep('Preparing upload…')
      const uRes = await fetch(`${WORKER}/api/matches/${id}/upload-url`, { method: 'POST' })
      const uData = await uRes.json()
      if (!uRes.ok) throw new Error(uData.error || 'Could not get upload URL')

      // 4 — upload the file straight to R2 with progress
      setStep('Uploading your match…')
      await putWithProgress(uData.upload_url, file, setPct)

      // 5 — trigger processing
      setStep('Starting analysis…')
      const dRes = await fetch(`${WORKER}/api/matches/${id}/uploaded`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ r2_key: uData.key }),
      })
      if (!dRes.ok) { const d = await dRes.json(); throw new Error(d.error || 'Could not start analysis') }

      setStage('done')
    } catch (e) {
      setError(e.message); setStage('form')
    }
  }

  const optIn = matchId ? `https://wa.me/${WABA}?text=${encodeURIComponent(`PADEL OPTIN ${matchId}`)}` : '#'

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid var(--border)', position: 'sticky', top: 0, background: 'var(--bg)', zIndex: 10 }}>
        <div style={{ fontSize: '17px', fontWeight: '800', letterSpacing: '-0.5px' }}>Upload a Match</div>
        <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '1px' }}>
          Recorded on any court, anywhere — get your report on WhatsApp
        </div>
      </div>

      <div style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

        {stage === 'done' ? (
          <div className="card" style={{ textAlign: 'center', padding: '28px 18px' }}>
            <div style={{ fontSize: '40px', marginBottom: '10px' }}>🎾</div>
            <div style={{ fontSize: '17px', fontWeight: '800', marginBottom: '6px' }}>Match uploaded!</div>
            <p style={{ color: 'var(--muted)', fontSize: '13px', lineHeight: 1.6, marginBottom: '18px' }}>
              We're analysing it now. Your heatmap, stats and highlights arrive on WhatsApp in a few minutes.
            </p>
            <a href={optIn} target="_blank" rel="noreferrer" className="btn-primary" style={{ display: 'block', textDecoration: 'none', textAlign: 'center' }}>
              Tap to get it on WhatsApp
            </a>
            <button className="btn-ghost" style={{ marginTop: '10px', width: '100%' }}
              onClick={() => { setStage('form'); setFile(null); setPct(0); setMatchId(null) }}>
              Upload another
            </button>
          </div>
        ) : stage === 'uploading' ? (
          <div className="card" style={{ textAlign: 'center', padding: '26px 18px' }}>
            <div style={{ fontSize: '13px', fontWeight: '700', color: 'var(--hot)', marginBottom: '14px' }}>{step}</div>
            <div style={{ height: '10px', background: 'var(--bg)', borderRadius: '6px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${Math.round(pct * 100)}%`, background: 'var(--hot)', transition: 'width .2s' }} />
            </div>
            <div style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '8px' }}>{Math.round(pct * 100)}%</div>
            <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '12px' }}>Keep this screen open until it finishes.</p>
          </div>
        ) : (
          <>
            <label className="card" style={{ display: 'block', textAlign: 'center', padding: '24px 16px', cursor: 'pointer', borderStyle: file ? 'solid' : 'dashed' }}>
              <input type="file" accept="video/*" capture="environment" style={{ display: 'none' }}
                onChange={e => setFile(e.target.files?.[0] || null)} />
              <div style={{ fontSize: '30px', marginBottom: '8px' }}>{file ? '🎬' : '⬆️'}</div>
              <div style={{ fontSize: '14px', fontWeight: '700' }}>{file ? file.name : 'Choose your match video'}</div>
              <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '4px' }}>
                {file ? `${(file.size / 1e6).toFixed(0)} MB — tap to change` : 'from your camera roll'}
              </div>
            </label>

            <div>
              <label style={{ fontSize: '12px', fontWeight: '700', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.5px' }}>Court</label>
              <select value={courtId} onChange={e => setCourtId(e.target.value)}
                style={{ width: '100%', marginTop: '7px', background: 'var(--bg-elev)', border: '1.5px solid var(--border)', borderRadius: '12px', color: 'var(--text)', fontSize: '15px', padding: '13px 14px' }}>
                {courts.length === 0 && <option value="">No courts found</option>}
                {courts.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: '700', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.5px' }}>Playing partners (optional)</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '7px' }}>
                {partners.map((p, i) => (
                  <input key={i} type="tel" placeholder={`Player ${i + 2} WhatsApp number`} value={p}
                    onChange={e => setPartners(partners.map((x, j) => j === i ? e.target.value : x))} />
                ))}
              </div>
            </div>

            {error && <div className="card" style={{ color: 'var(--danger)', fontSize: '13px', fontWeight: 600, borderColor: 'var(--danger)' }}>⚠️ {error}</div>}

            <button className="btn-primary" onClick={start} disabled={!file}>Upload &amp; analyse</button>
          </>
        )}
      </div>
    </div>
  )
}
