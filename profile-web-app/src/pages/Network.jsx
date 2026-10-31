import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, mediaUrl } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Button, Card } from '../components/ui'

export function Network() {
  const { user } = useAuth()
  const toast = useToast()
  const [people, setPeople] = useState([])
  const [query, setQuery] = useState('')

  async function load(q = '') {
    const qs = q ? `?q=${encodeURIComponent(q)}` : ''
    const rows = await api(`/api/network/people${qs}`)
    setPeople(rows)
  }

  useEffect(() => {
    load().catch((err) => toast.push(err.message, 'error'))
  }, [toast])

  async function follow(person) {
    try {
      const updated = await api(`/api/network/follow/${person.username}`, { method: 'POST' })
      setPeople((rows) => rows.map((row) => (row.id === updated.id ? { ...row, ...updated } : row)))
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  return (
    <div className="stack">
      <div className="page-title">
        <h1>Network</h1>
        <p>Follow other professionals and grow your circle.</p>
      </div>
      <input
        placeholder="Search by name or username"
        value={query}
        onChange={(event) => {
          const value = event.target.value
          setQuery(value)
          load(value).catch((err) => toast.push(err.message, 'error'))
        }}
        style={{ maxWidth: 360, borderRadius: 12, border: '1px solid var(--line)', padding: '10px 12px' }}
      />
      <div className="grid grid-2">
        {people.map((person) => (
          <Card key={person.id}>
            <div className="row space">
              <div className="row">
                <img className="avatar avatar-sm" src={mediaUrl(person.photo_path)} alt="" />
                <div>
                  <Link to={`/u/${person.username}`}><strong>{person.full_name || person.username}</strong></Link>
                  <p className="muted">@{person.username} · {person.headline}</p>
                  <p className="muted">{person.followers} followers · {person.following} following</p>
                </div>
              </div>
              {user?.id !== person.id ? (
                <Button type="button" variant={person.is_following ? 'ghost' : 'primary'} onClick={() => follow(person)}>
                  {person.is_following ? 'Following' : 'Follow'}
                </Button>
              ) : <span className="badge">You</span>}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
