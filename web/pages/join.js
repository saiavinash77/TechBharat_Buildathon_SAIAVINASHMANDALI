import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'

export default function Join() {
  const router = useRouter()
  const { token } = router.query
  const [invite, setInvite] = useState(null)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [github, setGithub] = useState('')
  const API = process.env.NEXT_PUBLIC_API_BASE || ''

  useEffect(() => {
    if (!token) return
    fetch(`${API}/join?token=${encodeURIComponent(token)}`).then(r => r.json()).then(setInvite).catch(e => console.error(e))
  }, [token])

  async function submit(e) {
    e.preventDefault()
    try {
      const res = await fetch(`${API}/join`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, name, email, github_handle: github || null })
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      alert('Joined ' + data.org_id)
      router.push('/')
    } catch (err) {
      alert('Join failed: ' + err.message)
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <h1>Join</h1>
      <div>Token: <strong>{token}</strong></div>
      {invite && <div>Invite to <strong>{invite.org_id}</strong> from <em>{invite.inviter_name}</em></div>}
      <form onSubmit={submit} style={{ marginTop: 12 }}>
        <div><label>Name<br/><input value={name} onChange={e=>setName(e.target.value)} required/></label></div>
        <div><label>Email<br/><input value={email} onChange={e=>setEmail(e.target.value)} type="email" required/></label></div>
        <div><label>GitHub handle<br/><input value={github} onChange={e=>setGithub(e.target.value)}/></label></div>
        <div style={{ marginTop: 8 }}><button type="submit">Join</button></div>
      </form>
    </div>
  )
}
