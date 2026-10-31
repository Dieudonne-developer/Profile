import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Button, Card, Field } from '../components/ui'

const TABS = ['About', 'Photo', 'Experience', 'Education', 'Skills', 'Languages']

const emptyExperience = {
  title: '', company: '', location: '', start_date: '', end_date: '', is_current: false, description: '',
}
const emptyEducation = {
  institution: '', degree: '', field: '', start_date: '', end_date: '', description: '',
}

export function Editor() {
  const { profile, refresh } = useAuth()
  const toast = useToast()
  const [tab, setTab] = useState('About')
  const [form, setForm] = useState(profile)
  const [tone, setTone] = useState('professional')
  const [items, setItems] = useState({ experience: [], education: [], skills: [], languages: [] })

  useEffect(() => {
    setForm(profile)
  }, [profile])

  useEffect(() => {
    Promise.all([
      api('/api/experience'),
      api('/api/education'),
      api('/api/skills'),
      api('/api/languages'),
    ]).then(([experience, education, skills, languages]) => {
      setItems({ experience, education, skills, languages })
    }).catch((err) => toast.push(err.message, 'error'))
  }, [])

  function update(event) {
    const { name, value, type, checked } = event.target
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  async function saveAbout(event) {
    event.preventDefault()
    try {
      const saved = await api('/api/profile/me', {
        method: 'PUT',
        body: JSON.stringify({
          full_name: form.full_name,
          headline: form.headline,
          bio: form.bio,
          location: form.location,
          phone: form.phone,
          public_email: form.public_email,
          website: form.website,
          github: form.github,
          linkedin: form.linkedin,
          twitter: form.twitter,
          birthday: form.birthday || '2002-01-01',
          is_public: form.is_public,
        }),
      })
      setForm(saved)
      await refresh()
      toast.push('Profile saved')
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function improveBio() {
    try {
      const result = await api('/api/ai/improve', {
        method: 'POST',
        body: JSON.stringify({ kind: 'bio', text: form.bio, tone }),
      })
      setForm((current) => ({ ...current, bio: result.improved }))
      toast.push(`Rewritten with ${result.provider}`)
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function uploadPhoto(event) {
    const file = event.target.files?.[0]
    if (!file) return
    const data = new FormData()
    data.append('file', file)
    try {
      await api('/api/profile/photo', { method: 'POST', body: data })
      await refresh()
      toast.push('Photo updated')
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function rotateShare() {
    try {
      const saved = await api('/api/profile/share-token', { method: 'POST' })
      setForm(saved)
      await refresh()
      toast.push('New share link created')
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function copyShare() {
    try {
      const url = `${window.location.origin}/s/${form.share_token}`
      await navigator.clipboard.writeText(url)
      toast.push('Share URL copied')
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  return (
    <div className="stack">
      <div className="page-title">
        <h1>Edit profile</h1>
        <p>Keep your public story, photo, and credentials up to date.</p>
      </div>
      <div className="tabs">
        {TABS.map((name) => (
          <button
            key={name}
            className="btn btn-ghost"
            type="button"
            aria-selected={tab === name}
            onClick={() => setTab(name)}
          >
            {name}
          </button>
        ))}
      </div>

      {tab === 'About' && !form ? (
        <Card><p>Loading profile…</p></Card>
      ) : null}

      {tab === 'About' && form ? (
        <Card>
          <form className="stack" onSubmit={saveAbout}>
            <div className="grid grid-2">
              <Field label="Full name"><input name="full_name" value={form.full_name || ''} onChange={update} /></Field>
              <Field label="Headline"><input name="headline" value={form.headline || ''} onChange={update} /></Field>
              <Field label="Birthday">
                <input type="date" name="birthday" value={form.birthday || '2002-01-01'} onChange={update} />
              </Field>
              <Field label="Location"><input name="location" value={form.location || ''} onChange={update} /></Field>
              <Field label="Public email"><input name="public_email" value={form.public_email || ''} onChange={update} /></Field>
              <Field label="Phone"><input name="phone" value={form.phone || ''} onChange={update} /></Field>
              <Field label="Website"><input name="website" value={form.website || ''} onChange={update} /></Field>
              <Field label="GitHub"><input name="github" value={form.github || ''} onChange={update} /></Field>
              <Field label="LinkedIn"><input name="linkedin" value={form.linkedin || ''} onChange={update} /></Field>
              <Field label="Twitter / X"><input name="twitter" value={form.twitter || ''} onChange={update} /></Field>
            </div>
            <Field label="Bio">
              <textarea name="bio" value={form.bio || ''} onChange={update} />
            </Field>
            <div className="row">
              <select value={tone} onChange={(e) => setTone(e.target.value)}>
                <option value="professional">Professional</option>
                <option value="confident">Confident</option>
                <option value="warm">Warm</option>
              </select>
              <Button variant="ghost" type="button" onClick={improveBio}>Improve with AI</Button>
              <label className="row">
                <input type="checkbox" name="is_public" checked={!!form.is_public} onChange={update} />
                Public profile
              </label>
            </div>
            <div className="row">
              <Button type="submit">Save about</Button>
              <Button variant="ghost" type="button" onClick={copyShare}>Copy share link</Button>
              <Button variant="ghost" type="button" onClick={rotateShare}>Rotate share token</Button>
            </div>
          </form>
        </Card>
      ) : null}

      {tab === 'Photo' ? (
        <Card>
          <Avatar src={profile?.photo_path} alt={profile?.full_name} size="avatar-lg" />
          <p className="muted">JPG, PNG or WebP, up to 5 MB. This is the photo shown on your public profile and CV workspace.</p>
          <input type="file" accept="image/*" onChange={uploadPhoto} />
        </Card>
      ) : null}

      {tab === 'Experience' ? (
        <CrudList
          title="Experience"
          path="/api/experience"
          rows={items.experience}
          setRows={(experience) => setItems((current) => ({ ...current, experience }))}
          blank={emptyExperience}
          fields={[
            ['title', 'Title'],
            ['company', 'Company'],
            ['location', 'Location'],
            ['start_date', 'Start'],
            ['end_date', 'End'],
            ['is_current', 'Current role', 'checkbox'],
            ['description', 'Description', 'textarea'],
          ]}
        />
      ) : null}
      {tab === 'Education' ? (
        <CrudList
          title="Education"
          path="/api/education"
          rows={items.education}
          setRows={(education) => setItems((current) => ({ ...current, education }))}
          blank={emptyEducation}
          fields={[
            ['institution', 'Institution'],
            ['degree', 'Degree'],
            ['field', 'Field'],
            ['start_date', 'Start'],
            ['end_date', 'End'],
            ['description', 'Description', 'textarea'],
          ]}
        />
      ) : null}
      {tab === 'Skills' ? (
        <CrudList
          title="Skills"
          path="/api/skills"
          rows={items.skills}
          setRows={(skills) => setItems((current) => ({ ...current, skills }))}
          blank={{ name: '', category: 'General', level: 70 }}
          fields={[
            ['name', 'Skill'],
            ['category', 'Category'],
            ['level', 'Level (0-100)'],
          ]}
        />
      ) : null}
      {tab === 'Languages' ? (
        <CrudList
          title="Languages"
          path="/api/languages"
          rows={items.languages}
          setRows={(languages) => setItems((current) => ({ ...current, languages }))}
          blank={{ name: '', proficiency: 'Professional' }}
          fields={[
            ['name', 'Language'],
            ['proficiency', 'Proficiency'],
          ]}
        />
      ) : null}
    </div>
  )
}

function CrudList({ title, path, rows, setRows, blank, fields }) {
  const toast = useToast()
  const [draft, setDraft] = useState(blank)
  const [editing, setEditing] = useState(null)

  function update(event) {
    const { name, value, type, checked } = event.target
    setDraft((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : name === 'level' ? Number(value) : value,
    }))
  }

  async function save(event) {
    event.preventDefault()
    const payload = { ...blank, ...draft }
    if (payload.end_date === '') payload.end_date = null
    try {
      const saved = editing
        ? await api(`${path}/${editing}`, { method: 'PUT', body: JSON.stringify(payload) })
        : await api(path, { method: 'POST', body: JSON.stringify(payload) })
      setRows(editing ? rows.map((row) => (row.id === saved.id ? saved : row)) : [...rows, saved])
      setDraft(blank)
      setEditing(null)
      toast.push(`${title} saved`)
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  async function remove(id) {
    try {
      await api(`${path}/${id}`, { method: 'DELETE' })
      setRows(rows.filter((row) => row.id !== id))
    } catch (err) {
      toast.push(err.message, 'error')
    }
  }

  return (
    <Card>
      <h2>{title}</h2>
      <div className="stack">
        {rows.map((row) => (
          <div className="row space" key={row.id}>
            <div>
              <strong>{row.title || row.institution || row.name}</strong>
              <p className="muted">{row.company || row.degree || row.category || row.proficiency}</p>
            </div>
            <div className="row">
              <Button variant="ghost" type="button" onClick={() => { setEditing(row.id); setDraft(row) }}>Edit</Button>
              <Button variant="danger" type="button" onClick={() => remove(row.id)}>Delete</Button>
            </div>
          </div>
        ))}
      </div>
      <form className="stack" style={{ marginTop: 16 }} onSubmit={save}>
        {fields.map(([name, label, kind]) => (
          <Field key={name} label={label}>
            {kind === 'textarea' ? (
              <textarea name={name} value={draft[name] || ''} onChange={update} />
            ) : kind === 'checkbox' ? (
              <input type="checkbox" name={name} checked={!!draft[name]} onChange={update} />
            ) : (
              <input name={name} value={draft[name] ?? ''} onChange={update} />
            )}
          </Field>
        ))}
        <Button type="submit">{editing ? 'Update' : 'Add'}</Button>
      </form>
    </Card>
  )
}
