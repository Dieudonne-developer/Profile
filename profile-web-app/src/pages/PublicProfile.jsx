import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  BrainCircuit,
  CalendarClock,
  Code2,
  Cpu,
  Mail,
  MapPin,
  ScanLine,
} from 'lucide-react'
import { api, downloadCv, trackEvent } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Button, ErrorText, Field } from '../components/ui'
import { SectionTitle, VCardShell } from '../components/VCardLayout'
import { EducationBlock, ExperienceBlock, LanguagesBlock, SkillsBlock } from '../components/ProfileView'
import { ProjectCard } from '../components/ProjectCard'
import { rangeLabel } from '../lib/format'

const SERVICE_ICONS = [BrainCircuit, ScanLine, Cpu, Code2]

function servicesFrom(data) {
  const skills = data?.skills || []
  const grouped = skills.reduce((acc, skill) => {
    const key = skill.category || 'General'
    acc[key] = acc[key] || []
    acc[key].push(skill.name)
    return acc
  }, {})
  const fromSkills = Object.entries(grouped).slice(0, 4).map(([title, names]) => ({
    title,
    text: names.slice(0, 4).join(', '),
  }))
  if (fromSkills.length >= 4) return fromSkills
  return [
    { title: 'Machine Learning', text: 'Classification, regression, preprocessing, training, and evaluation.' },
    { title: 'Computer vision', text: 'Image classification with PyTorch and EfficientNet-B0.' },
    { title: 'Data science', text: 'Feature work, correlation analysis, and practical prediction tools.' },
    { title: 'Applied software', text: 'FastAPI, React, and Node.js to put models into usable applications.' },
    ...fromSkills,
  ].slice(0, 4)
}

export function PublicProfile({ share = false, ownerUsername }) {
  const params = useParams()
  const username = ownerUsername || params.username
  const { token } = params
  const { user } = useAuth()
  const toast = useToast()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [contact, setContact] = useState({ name: '', email: '', subject: '', message: '' })
  const [sending, setSending] = useState(false)

  async function load() {
    try {
      const path = share ? `/api/s/${token}` : `/api/u/${username}`
      const bundle = await api(path)
      setData(bundle)
      trackEvent(bundle.user.username, 'profile_view')
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    load()
  }, [username, token, share])

  async function sendMessage(event) {
    event.preventDefault()
    setSending(true)
    try {
      await api(`/api/contact/${data.user.username}`, {
        method: 'POST',
        body: JSON.stringify(contact),
      })
      setContact({ name: '', email: '', subject: '', message: '' })
      toast.push('Message sent. Thank you.')
    } catch (err) {
      toast.push(err.message, 'error')
    } finally {
      setSending(false)
    }
  }

  if (error) {
    return (
      <div className="landing">
        <ErrorText error={error} />
        <Link className="btn btn-primary" to="/">Back home</Link>
      </div>
    )
  }
  if (!data) {
    return <div className="landing"><p>Loading profile…</p></div>
  }

  const isOwner = user?.id === data.user.id
  const services = servicesFrom(data)
  const bioParts = (data.profile.bio || '').split(/\n\n+/)

  return (
    <VCardShell
      profile={data.profile}
      user={data.user}
      onDownload={() => downloadCv(data.user.username).catch((err) => toast.push(err.message, 'error'))}
    >
      <section className="panel" id="about">
        <SectionTitle lead="About" accent="Me" />
        {bioParts.map((part) => (
          <p key={part.slice(0, 24)} style={{ whiteSpace: 'pre-wrap' }}>{part}</p>
        ))}
        <div className="row" style={{ marginTop: 12, flexWrap: 'wrap' }}>
          <Link className="btn btn-primary" to="/lab">Try the ML lab</Link>
          <a className="btn btn-ghost" href="#portfolio">View My Projects</a>
          <Button
            type="button"
            onClick={() => downloadCv(data.user.username).catch((err) => toast.push(err.message, 'error'))}
          >
            Download My CV
          </Button>
          <a className="btn btn-ghost" href="#contact">Contact Me</a>
          {data.profile.github ? (
            <a className="btn btn-ghost" href={data.profile.github} target="_blank" rel="noreferrer">View GitHub</a>
          ) : null}
          {isOwner ? <Link className="btn btn-ghost" to="/app">Dashboard</Link> : null}
        </div>
      </section>

      <section className="panel" id="services">
        <SectionTitle lead="My" accent="Services" />
        <div className="services">
          {services.map((service, index) => {
            const Icon = SERVICE_ICONS[index] || Code2
            return (
              <article className="service" key={service.title}>
                <Icon size={34} strokeWidth={1.4} />
                <h3>{service.title}</h3>
                <p>{service.text}</p>
              </article>
            )
          })}
        </div>
      </section>

      <section className="panel" id="resume">
        <SectionTitle lead="My" accent="Resume" />
        <div className="stack">
          <ExperienceBlock items={data.experiences} />
          <EducationBlock items={data.education} />
          <div className="grid grid-2">
            <SkillsBlock items={data.skills} />
            <LanguagesBlock items={data.languages} />
          </div>
        </div>
      </section>

      <section className="panel" id="portfolio">
        <SectionTitle lead="My" accent="Portfolio" />
        <div className="portfolio-grid">
          {data.projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onChange={(next) => setData((current) => ({
                ...current,
                projects: current.projects.map((row) => row.id === next.id ? next : row),
              }))}
            />
          ))}
        </div>
      </section>

      <section className="panel" id="blog">
        <SectionTitle lead="Latest" accent="Notes" />
        {(data.experiences || []).slice(0, 2).map((item) => (
          <article key={item.id} style={{ marginBottom: 18 }}>
            <h3 style={{ margin: '0 0 6px' }}>{item.title}</h3>
            <p className="muted">{rangeLabel(item.start_date, item.end_date, item.is_current)}</p>
            <p>{item.description}</p>
          </article>
        ))}
      </section>

      <section className="panel" id="contact">
        <SectionTitle lead="Get in" accent="Touch" />
        <p>
          I am looking for junior and internship roles in machine learning, AI engineering, and data science.
          Send a message here and I will receive it in my admin inbox.
        </p>
        {data.profile.public_email ? (
          <p className="row">
            <Mail size={16} />
            <a href={`mailto:${data.profile.public_email}`}>{data.profile.public_email}</a>
          </p>
        ) : null}
        {data.profile.location ? <p className="row"><MapPin size={16} /> {data.profile.location}</p> : null}
        {data.profile.phone ? (
          <p className="row"><CalendarClock size={16} /> {data.profile.phone}</p>
        ) : null}
        <form className="stack" style={{ marginTop: 18, maxWidth: 560 }} onSubmit={sendMessage}>
          <Field label="Your name">
            <input
              value={contact.name}
              onChange={(event) => setContact((current) => ({ ...current, name: event.target.value }))}
              required
              minLength={2}
            />
          </Field>
          <Field label="Your email">
            <input
              type="email"
              value={contact.email}
              onChange={(event) => setContact((current) => ({ ...current, email: event.target.value }))}
              required
            />
          </Field>
          <Field label="Subject">
            <input
              value={contact.subject}
              onChange={(event) => setContact((current) => ({ ...current, subject: event.target.value }))}
              placeholder="Internship, collaboration, question…"
            />
          </Field>
          <Field label="Message">
            <textarea
              value={contact.message}
              onChange={(event) => setContact((current) => ({ ...current, message: event.target.value }))}
              required
              minLength={10}
            />
          </Field>
          <Button type="submit" disabled={sending}>{sending ? 'Sending…' : 'Send message'}</Button>
        </form>
      </section>
    </VCardShell>
  )
}
