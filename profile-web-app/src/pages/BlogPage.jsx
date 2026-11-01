import { useEffect, useState } from 'react'
import { api } from '../api'
import { useToast } from '../context/ToastContext'
import { Button, Card, Empty, Field } from '../components/ui'
import { timeAgo } from '../lib/format'

const blank = {
  title: '',
  summary: '',
  body: '',
  published: true,
}

export function BlogPage() {
  const toast = useToast()
  const [posts, setPosts] = useState([])
  const [form, setForm] = useState(blank)
  const [editing, setEditing] = useState(null)
  const [tone, setTone] = useState('professional')

  useEffect(() => {
    api('/api/posts').then(setPosts).catch((err) => toast.push(err.message, 'error'))
  }, [toast])

  function update(event) {
    const { name, value, type, checked } = event.target
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  async function save(event) {
    event.preventDefault()
    const body = JSON.stringify(form)
    try {
      const saved = editing
        ? await api(`/api/posts/${editing}`, { method: 'PUT', body })
        : await api('/api/posts', { method: 'POST', body })
      setPosts((rows) => (editing ? rows.map((row) => (row.id === saved.id ? saved : row)) : [saved, ...rows]))
      setForm(blank)
      setEditing(null)
      toast.push('Post saved')
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function improve() {
    try {
      const result = await api('/api/ai/improve', {
        method: 'POST',
        body: JSON.stringify({ kind: 'project', text: form.body || form.summary, tone }),
      })
      setForm((current) => ({ ...current, body: result.improved }))
      toast.push(`Rewritten with ${result.provider}`)
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function remove(post) {
    try {
      await api(`/api/posts/${post.id}`, { method: 'DELETE' })
      setPosts((rows) => rows.filter((row) => row.id !== post.id))
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  return (
    <div className="stack">
      <div className="page-title">
        <h1>Blog</h1>
        <p>Write notes that appear on your public profile under Blog.</p>
      </div>
      <Card>
        <h2>{editing ? 'Edit post' : 'Write a post'}</h2>
        <form className="stack" onSubmit={save}>
          <Field label="Title"><input name="title" value={form.title} onChange={update} required /></Field>
          <Field label="Summary"><input name="summary" value={form.summary} onChange={update} /></Field>
          <Field label="Body"><textarea name="body" value={form.body} onChange={update} rows={8} /></Field>
          <label className="row">
            <input type="checkbox" name="published" checked={form.published} onChange={update} /> Published
          </label>
          <div className="row">
            <select value={tone} onChange={(e) => setTone(e.target.value)}>
              <option value="professional">Professional</option>
              <option value="confident">Confident</option>
              <option value="warm">Warm</option>
            </select>
            <Button variant="ghost" type="button" onClick={improve}>Improve writing</Button>
            <Button type="submit">Save post</Button>
            {editing ? (
              <Button
                variant="ghost"
                type="button"
                onClick={() => {
                  setEditing(null)
                  setForm(blank)
                }}
              >
                Cancel
              </Button>
            ) : null}
          </div>
        </form>
      </Card>
      {posts.length ? posts.map((post) => (
        <Card key={post.id}>
          <div className="row space">
            <div>
              <strong>{post.title}</strong>
              <p className="muted">
                {post.published ? 'Published' : 'Draft'} · {timeAgo(post.created_at)}
              </p>
              {post.summary ? <p>{post.summary}</p> : null}
            </div>
            <div className="row">
              <Button
                variant="ghost"
                type="button"
                onClick={() => {
                  setEditing(post.id)
                  setForm({
                    title: post.title,
                    summary: post.summary || '',
                    body: post.body || '',
                    published: post.published,
                  })
                }}
              >
                Edit
              </Button>
              <Button variant="ghost" type="button" onClick={() => remove(post)}>Delete</Button>
            </div>
          </div>
        </Card>
      )) : <Empty title="No posts yet." text="Write a note and publish it to the public Blog section." />}
    </div>
  )
}
