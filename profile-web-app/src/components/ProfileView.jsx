import { AtSign, Code2, Globe, Link2, Mail, MapPin, Phone } from 'lucide-react'
import { Avatar } from './ui'
import { groupBy, rangeLabel } from '../lib/format'

export function ProfileHero({ profile, user, actions }) {
  return (
    <section className="hero-public">
      <Avatar src={profile.photo_path} alt={profile.full_name} size="avatar-lg" />
      <div>
        <span className="badge">{profile.is_public ? 'Public profile' : 'Private'}</span>
        <h1 style={{ margin: '8px 0 4px' }}>{profile.full_name || user?.username}</h1>
        <p>{profile.headline}</p>
        <div className="row" style={{ marginTop: 12, color: '#c9d7e3' }}>
          {profile.location ? <span className="row"><MapPin size={16} /> {profile.location}</span> : null}
          {profile.public_email ? <span className="row"><Mail size={16} /> {profile.public_email}</span> : null}
          {profile.phone ? <span className="row"><Phone size={16} /> {profile.phone}</span> : null}
        </div>
        <div className="row" style={{ marginTop: 16 }}>{actions}</div>
      </div>
    </section>
  )
}

export function ContactLinks({ profile }) {
  const links = [
    [profile.website, 'Website', Globe],
    [profile.github, 'GitHub', Code2],
    [profile.linkedin, 'LinkedIn', Link2],
    [profile.twitter, 'X / Twitter', AtSign],
  ].filter(([href]) => href)
  if (!links.length) return null
  return (
    <div className="row">
      {links.map(([href, label, Icon]) => (
        <a key={label} className="btn btn-ghost" href={href} target="_blank" rel="noreferrer">
          <Icon size={16} /> {label}
        </a>
      ))}
    </div>
  )
}

export function TimelineList({ title, items, render }) {
  if (!items?.length) return null
  return (
    <section>
      <h2 className="section-title">{title}</h2>
      <div className="timeline">
        {items.map((item) => (
          <article key={item.id}>{render(item)}</article>
        ))}
      </div>
    </section>
  )
}

export function ExperienceBlock({ items }) {
  return (
    <TimelineList
      title="Experience"
      items={items}
      render={(item) => (
        <>
          <h3 style={{ margin: 0 }}>{item.title}</h3>
          <p className="muted">
            {item.company} · {rangeLabel(item.start_date, item.end_date, item.is_current)}
            {item.location ? ` · ${item.location}` : ''}
          </p>
          <p>{item.description}</p>
        </>
      )}
    />
  )
}

export function EducationBlock({ items }) {
  return (
    <TimelineList
      title="Education"
      items={items}
      render={(item) => (
        <>
          <h3 style={{ margin: 0 }}>{item.degree || item.institution}</h3>
          <p className="muted">
            {item.institution} · {item.field} · {rangeLabel(item.start_date, item.end_date)}
          </p>
          <p>{item.description}</p>
        </>
      )}
    />
  )
}

export function SkillsBlock({ items }) {
  if (!items?.length) return null
  const grouped = groupBy(items, 'category')
  return (
    <section>
      <h2 className="section-title">Skills</h2>
      {Object.entries(grouped).map(([category, skills]) => (
        <div key={category} style={{ marginBottom: 16 }}>
          <h3>{category}</h3>
          {skills.map((skill) => (
            <div className="skill" key={skill.id}>
              <div className="row space">
                <span>{skill.name}</span>
                <span className="muted">{skill.level}%</span>
              </div>
              <div className="skill-bar">
                <span style={{ width: `${skill.level}%` }} />
              </div>
            </div>
          ))}
        </div>
      ))}
    </section>
  )
}

export function LanguagesBlock({ items }) {
  if (!items?.length) return null
  return (
    <section>
      <h2 className="section-title">Languages</h2>
      {items.map((item) => (
        <p key={item.id}>
          <strong>{item.name}</strong> · {item.proficiency}
        </p>
      ))}
    </section>
  )
}
