import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Button, Card, Empty } from '../components/ui'
import { timeAgo } from '../lib/format'

export function Messages() {
  const { user } = useAuth()
  const toast = useToast()
  const [items, setItems] = useState([])

  useEffect(() => {
    api('/api/contact/inbox').then(setItems).catch((err) => toast.push(err.message, 'error'))
  }, [toast])

  async function mark(id) {
    try {
      const saved = await api(`/api/contact/${user.username}/read/${id}`, { method: 'POST' })
      setItems((rows) => rows.map((row) => (row.id === saved.id ? saved : row)))
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  return (
    <div className="stack">
      <div className="page-title">
        <h1>Messages</h1>
        <p>People who wrote from the public contact form. A copy is also sent to your Gmail.</p>
      </div>
      {items.length ? items.map((item) => (
        <Card key={item.id}>
          <div className="row space">
            <div>
              <strong>{item.subject || 'Portfolio contact'}</strong>
              <p className="muted">{item.sender_name} · {item.sender_email} · {timeAgo(item.created_at)}</p>
              <p style={{ whiteSpace: 'pre-wrap' }}>{item.body}</p>
            </div>
            {!item.is_read ? <Button type="button" onClick={() => mark(item.id)}>Mark read</Button> : null}
          </div>
        </Card>
      )) : <Empty title="No messages yet" text="When someone submits the contact form, it will appear here." />}
    </div>
  )
}
