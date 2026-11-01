import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, downloadCv } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Button, Card } from '../components/ui'
import { ProjectCard } from '../components/ProjectCard'

export function Dashboard() {
  const { user, profile } = useAuth()
  const toast = useToast()
  const [stats, setStats] = useState(null)
  const [projects, setProjects] = useState([])
  const [notes, setNotes] = useState([])

  useEffect(() => {
    Promise.all([
      api('/api/analytics/summary'),
      api('/api/projects'),
      api('/api/notifications'),
    ]).then(([summary, mine, notifications]) => {
      setStats(summary)
      setProjects(mine)
      setNotes(notifications.slice(0, 4))
    }).catch((err) => toast.push(err.message, 'error'))
  }, [toast])

  async function copyShare() {
    const url = `${window.location.origin}/u/${user.username}`
    await navigator.clipboard.writeText(url)
    api('/api/analytics/track', {
      method: 'POST',
      body: JSON.stringify({ username: user.username, event_type: 'share', path: '/app' }),
    }).catch(() => {})
    toast.push('Public profile link copied')
  }

  return (
    <div className="stack">
      <div className="page-title">
        <h1>Overview</h1>
        <p>Your workspace for profile, projects, analytics, and sharing.</p>
      </div>
      <section className="card row space">
        <div className="row">
          <Avatar src={profile?.photo_path} alt={profile?.full_name} />
          <div>
            <h2 style={{ margin: 0 }}>{profile?.full_name}</h2>
            <p className="muted">{profile?.headline}</p>
            <p className="muted">@{user.username}</p>
          </div>
        </div>
        <div className="row">
          <Button type="button" onClick={copyShare}>Copy public link</Button>
          <Button variant="dark" type="button" onClick={() => downloadCv(user.username).catch((e) => toast.push(e.message, 'error'))}>
            Download CV
          </Button>
          <Link className="btn btn-ghost" to="/app/profile">Edit profile</Link>
          <Link className="btn btn-ghost" to="/app/ml">ML lab</Link>
          <Link className="btn btn-ghost" to="/app/messages">Messages</Link>
        </div>
      </section>
      <section className="grid stats-row">
        {[
          ['Profile views', stats?.profile_views ?? '—'],
          ['Unique visitors', stats?.unique_visitors ?? '—'],
          ['CV downloads', stats?.cv_downloads ?? '—'],
        ].map(([label, value]) => (
          <div className="stat" key={label}>
            <span className="muted">{label}</span>
            <b>{value}</b>
          </div>
        ))}
      </section>
      <div className="grid grid-2">
        <Card>
          <div className="row space">
            <h2>Featured projects</h2>
            <Link to="/app/projects">Manage</Link>
          </div>
          <div className="stack">
            {[
              ...projects.filter((item) => item.featured),
              ...projects.filter((item) => !item.featured),
            ].slice(0, 2).map((project) => (
              <ProjectCard key={project.id} project={project} onChange={(next) => setProjects((rows) => rows.map((row) => row.id === next.id ? next : row))} />
            ))}
          </div>
        </Card>
        <Card>
          <div className="row space">
            <h2>Notifications</h2>
            <Link to="/app/notifications">See all</Link>
          </div>
          {notes.length ? notes.map((item) => (
            <p key={item.id}><strong>{item.title}</strong><br /><span className="muted">{item.body}</span></p>
          )) : <p className="muted">No notifications yet. Follows, likes, and comments will appear here.</p>}
        </Card>
      </div>
    </div>
  )
}
