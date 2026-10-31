import { useEffect, useState } from 'react'
import { api } from '../api'
import { useToast } from '../context/ToastContext'
import { Button, Card, Field } from '../components/ui'
import { ProjectCard } from '../components/ProjectCard'

const blank = {
  title: '',
  summary: '',
  description: '',
  tags: '',
  repo_url: '',
  live_url: '',
  featured: false,
}

export function ProjectsPage() {
  const toast = useToast()
  const [projects, setProjects] = useState([])
  const [form, setForm] = useState(blank)
  const [editing, setEditing] = useState(null)
  const [tone, setTone] = useState('professional')

  useEffect(() => {
    api('/api/projects').then(setProjects).catch((err) => toast.push(err.message, 'error'))
  }, [toast])

  function update(event) {
    const { name, value, type, checked } = event.target
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  function payload() {
    return {
      ...form,
      tags: String(form.tags || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
    }
  }

  async function save(event) {
    event.preventDefault()
    const body = JSON.stringify(payload())
    try {
      const saved = editing
        ? await api(`/api/projects/${editing}`, { method: 'PUT', body })
        : await api('/api/projects', { method: 'POST', body })
      setProjects((rows) => (editing ? rows.map((row) => (row.id === saved.id ? saved : row)) : [saved, ...rows]))
      setForm(blank)
      setEditing(null)
      toast.push('Project saved')
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function improve() {
    try {
      const result = await api('/api/ai/improve', {
        method: 'POST',
        body: JSON.stringify({ kind: 'project', text: form.description || form.summary, tone }),
      })
      setForm((current) => ({ ...current, description: result.improved }))
      toast.push(`Rewritten with ${result.provider}`)
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function remove(project) {
    try {
      await api(`/api/projects/${project.id}`, { method: 'DELETE' })
      setProjects((rows) => rows.filter((row) => row.id !== project.id))
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  return (
    <div className="stack">
      <div className="page-title">
        <h1>Projects</h1>
        <p>Showcase work on your public profile and the community feed.</p>
      </div>
      <Card>
        <h2>{editing ? 'Edit project' : 'Add a project'}</h2>
        <form className="stack" onSubmit={save}>
          <Field label="Title"><input name="title" value={form.title} onChange={update} required /></Field>
          <Field label="Summary"><input name="summary" value={form.summary} onChange={update} /></Field>
          <Field label="Description"><textarea name="description" value={form.description} onChange={update} /></Field>
          <Field label="Tags (comma separated)"><input name="tags" value={form.tags} onChange={update} /></Field>
          <div className="grid grid-2">
            <Field label="Repository URL"><input name="repo_url" value={form.repo_url} onChange={update} /></Field>
            <Field label="Live URL"><input name="live_url" value={form.live_url} onChange={update} /></Field>
          </div>
          <label className="row">
            <input type="checkbox" name="featured" checked={form.featured} onChange={update} /> Featured
          </label>
          <div className="row">
            <select value={tone} onChange={(e) => setTone(e.target.value)}>
              <option value="professional">Professional</option>
              <option value="confident">Confident</option>
              <option value="warm">Warm</option>
            </select>
            <Button variant="ghost" type="button" onClick={improve}>Improve description</Button>
            <Button type="submit">Save project</Button>
          </div>
        </form>
      </Card>
      {projects.map((project) => (
        <ProjectCard
          key={project.id}
          project={project}
          canEdit
          onChange={(next) => setProjects((rows) => rows.map((row) => (row.id === next.id ? next : row)))}
          onEdit={(item) => {
            setEditing(item.id)
            setForm({ ...item, tags: (item.tags || []).join(', ') })
          }}
          onDelete={remove}
        />
      ))}
    </div>
  )
}
