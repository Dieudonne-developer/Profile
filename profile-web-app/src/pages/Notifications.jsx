import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useToast } from '../context/ToastContext'
import { Button, Card, Empty } from '../components/ui'
import { timeAgo } from '../lib/format'

export function Notifications() {
  const toast = useToast()
  const [items, setItems] = useState([])

  useEffect(() => {
    api('/api/notifications').then(setItems).catch((err) => toast.push(err.message, 'error'))
  }, [toast])

  async function mark(id) {
    try {
      const saved = await api(`/api/notifications/${id}/read`, { method: 'POST' })
      setItems((rows) => rows.map((row) => (row.id === saved.id ? saved : row)))
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function markAll() {
    try {
      await api('/api/notifications/read-all', { method: 'POST' })
      setItems((rows) => rows.map((row) => ({ ...row, is_read: true })))
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  return (
    <div className="stack">
      <div className="row space">
        <div className="page-title">
          <h1>Notifications</h1>
          <p>Follows, likes, and comments on your work.</p>
        </div>
        <Button variant="ghost" type="button" onClick={markAll}>Mark all read</Button>
      </div>
      {items.length ? items.map((item) => (
        <Card key={item.id}>
          <div className="row space">
            <div>
              <strong>{item.title}</strong>
              <p>{item.body}</p>
              <p className="muted">{timeAgo(item.created_at)} {item.is_read ? '' : '· Unread'}</p>
            </div>
            <div className="row">
              {item.link ? <Link className="btn btn-ghost" to={item.link}>Open</Link> : null}
              {!item.is_read ? <Button type="button" onClick={() => mark(item.id)}>Mark read</Button> : null}
            </div>
          </div>
        </Card>
      )) : <Empty title="You're all caught up" />}
    </div>
  )
}
