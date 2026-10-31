import { useState } from 'react'
import { Heart, MessageCircle } from 'lucide-react'
import { api } from '../api'
import { Button, Empty } from './ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { timeAgo } from '../lib/format'

export function ProjectCard({ project, onChange, canEdit, onEdit, onDelete }) {
  const { user } = useAuth()
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const [comments, setComments] = useState([])
  const [body, setBody] = useState('')

  async function toggleLike() {
    if (!user) return toast.push('Sign in to like projects', 'error')
    try {
      const updated = await api(`/api/projects/${project.id}/like`, { method: 'POST' })
      onChange?.(updated)
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function loadComments() {
    try {
      const rows = await api(`/api/projects/${project.id}/comments`)
      setComments(rows)
      setOpen(true)
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function addComment(event) {
    event.preventDefault()
    if (!user) return toast.push('Sign in to comment', 'error')
    try {
      await api(`/api/projects/${project.id}/comments`, {
        method: 'POST',
        body: JSON.stringify({ body }),
      })
      setBody('')
      await loadComments()
      onChange?.({ ...project, comments: (project.comments || 0) + 1 })
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  return (
    <article className="card">
      <div className="row space">
        <div>
          {project.featured ? <span className="badge">Featured</span> : null}
          <h3 style={{ margin: '6px 0' }}>{project.title}</h3>
          <p className="muted">
            {project.author ? `@${project.author}` : ''} {project.created_at ? `· ${timeAgo(project.created_at)}` : ''}
          </p>
        </div>
      </div>
      <p>{project.summary || project.description}</p>
      {project.description && project.summary ? <p className="muted">{project.description}</p> : null}
      <div className="tags" style={{ margin: '12px 0' }}>
        {(project.tags || []).map((tag) => (
          <span className="tag" key={tag}>{tag}</span>
        ))}
      </div>
      <div className="row space">
        <div className="row">
          <Button variant="ghost" type="button" onClick={toggleLike}>
            <Heart size={16} fill={project.liked ? 'currentColor' : 'none'} /> {project.likes || 0}
          </Button>
          <Button variant="ghost" type="button" onClick={loadComments}>
            <MessageCircle size={16} /> {project.comments || 0}
          </Button>
          {project.repo_url ? (
            <a className="btn btn-ghost" href={project.repo_url} target="_blank" rel="noreferrer">Repo</a>
          ) : null}
          {project.live_url ? (
            <a className="btn btn-ghost" href={project.live_url} target="_blank" rel="noreferrer">Live</a>
          ) : null}
        </div>
        {canEdit ? (
          <div className="row">
            <Button variant="ghost" type="button" onClick={() => onEdit(project)}>Edit</Button>
            <Button variant="danger" type="button" onClick={() => onDelete(project)}>Delete</Button>
          </div>
        ) : null}
      </div>
      {open ? (
        <div className="comments">
          {comments.length ? comments.map((item) => (
            <div className="comment" key={item.id}>
              <strong>@{item.author}</strong>
              <p>{item.body}</p>
            </div>
          )) : <Empty title="No comments yet" />}
          <form className="row" onSubmit={addComment}>
            <input
              style={{ flex: 1, borderRadius: 12, border: '1px solid var(--line)', padding: '10px 12px' }}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Write a comment"
              required
            />
            <Button type="submit">Post</Button>
          </form>
        </div>
      ) : null}
    </article>
  )
}
