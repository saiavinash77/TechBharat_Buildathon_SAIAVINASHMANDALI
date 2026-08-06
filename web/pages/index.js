import { useState, useEffect } from 'react'

export default function Home() {
  const [members, setMembers] = useState([])
  const [org, setOrg] = useState('demo-org')
  const API = process.env.NEXT_PUBLIC_API_BASE || ''

  useEffect(() => {
    // noop
  }, [])

  async function refreshMembers() {
    try {
      const res = await fetch(`${API}/orgs/${encodeURIComponent(org)}/members`)
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setMembers(data.members || [])
    } catch (err) {
      alert('Failed to fetch members: ' + err.message)
    }
  }

  return (
    <div style={{ padding: 24, fontFamily: 'Inter, system-ui, sans-serif' }}>
      <h1>Agentic UI (Next.js MVP)</h1>
      <p>Backend API: <code>{API || 'http://127.0.0.1:8000'}</code></p>
      <div style={{ marginTop: 16 }}>
        <label>Org ID: <input value={org} onChange={e => setOrg(e.target.value)} /></label>
        <button style={{ marginLeft: 8 }} onClick={refreshMembers}>Refresh Members</button>
      </div>
      <div style={{ marginTop: 16 }}>
        <h3>Members</h3>
        {members.length === 0 && <div style={{ color: '#666' }}>No members yet</div>}
        <ul>
          {members.map((m, i) => (
            <li key={i} style={{ marginBottom: 8 }}>
              <strong>{(m.user && (m.user.name || m.user.email)) || 'Unknown'}</strong>
              <div style={{ fontSize: 12, color: '#555' }}>{m.user && m.user.email} {m.user && m.user.github_handle ? ` • ${m.user.github_handle}` : ''}</div>
            </li>
          ))}
        </ul>
      </div>

      <div style={{ marginTop: 24 }}>
        <a href="/join?token=demo" style={{ marginRight: 12 }}>Open Join page (demo token)</a>
        <a href="/api/meetings">List Meetings (API)</a>
      </div>
    </div>
  )
}
