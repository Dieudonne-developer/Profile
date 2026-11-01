import { Download, Glasses, Globe, House, Send } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { mediaUrl, photoFallback } from '../api'
import { formatBirthday } from '../lib/format'
import { useAuth } from '../context/AuthContext'

function BrandIcon({ size = 16, children, ...props }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  )
}

function Github({ size = 16 }) {
  return (
    <BrandIcon size={size}>
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65S8.93 17.38 9 18v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </BrandIcon>
  )
}

function Twitter({ size = 16 }) {
  return (
    <BrandIcon size={size}>
      <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z" />
    </BrandIcon>
  )
}

function Linkedin({ size = 16 }) {
  return (
    <BrandIcon size={size}>
      <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z" />
      <rect width="4" height="12" x="2" y="9" />
      <circle cx="4" cy="4" r="2" />
    </BrandIcon>
  )
}

function Decor() {
  return (
    <>
      <span className="deco-ring a" />
      <span className="deco-ring b" />
      <span className="deco-ring c" />
      <span className="deco-sq" />
    </>
  )
}

export function VCardNav({ username, email, profile, hireHref }) {
  const location = useLocation()
  const { user } = useAuth()
  const home = username ? `/u/${username}` : '/'
  const item = (hash, label) => {
    const href = `${home}${hash}`
    const active = location.hash === hash || (hash === '#about' && location.hash === '')
    return (
      <a className={active ? 'active' : ''} href={href}>{label}</a>
    )
  }

  return (
    <header className="vcard-nav">
      <a className="vcard-home" href={`${home}#about`} aria-label="Home">
        <House size={22} color="white" fill="white" />
      </a>
      <nav className="vcard-nav-links">
        {item('#resume', 'Resume')}
        <Link to="/lab">ML lab</Link>
        {item('#portfolio', 'Portfolio')}
        {item('#blog', 'Blog')}
        {item('#contact', 'Contact')}
      </nav>
      <div className="vcard-social">
        {profile?.website ? <a href={profile.website} target="_blank" rel="noreferrer" aria-label="Website"><Globe size={16} /></a> : <Globe size={16} />}
        {profile?.twitter ? <a href={profile.twitter} target="_blank" rel="noreferrer" aria-label="Twitter"><Twitter size={16} /></a> : <Twitter size={16} />}
        {profile?.linkedin ? <a href={profile.linkedin} target="_blank" rel="noreferrer" aria-label="LinkedIn"><Linkedin size={16} /></a> : <Linkedin size={16} />}
        {profile?.github ? <a href={profile.github} target="_blank" rel="noreferrer" aria-label="GitHub"><Github size={16} /></a> : <Github size={16} />}
      </div>
      <a className="btn-hire" href={hireHref || (email ? `mailto:${email}` : user ? '/app' : '/login')}>
        Contact Me <Send size={14} />
      </a>
    </header>
  )
}

export function VCardSide({ profile, user, onDownload }) {
  const name = profile?.full_name || user?.username || 'Profile'
  const job = profile?.headline || 'Aspiring Machine Learning Engineer'
  const birthday = formatBirthday(profile?.birthday || '2002-01-01')
  const facts = [
    ['Name', name],
    ['Birthday', birthday],
    ['Job', job.split('·')[0].trim() || job],
    ['Email', profile?.public_email || user?.email || '—'],
    profile?.phone ? ['Phone', profile.phone] : ['Location', profile?.location || 'Remote'],
  ]

  return (
    <aside className="vcard-side">
      <div className="vcard-side-head">
        <h1>{name}</h1>
        <p>{job}</p>
      </div>
      <div className="vcard-photo-wrap">
        <img className="vcard-photo" src={mediaUrl(profile?.photo_path)} alt={name} onError={photoFallback} />
        <span className="vcard-badge" aria-hidden="true">
          <Glasses size={20} />
        </span>
      </div>
      <ul className="vcard-facts">
        {facts.map(([label, value]) => (
          <li key={label}>
            <span className="dot" />
            <span><b>{label}:</b> {value}</span>
          </li>
        ))}
      </ul>
      <button className="btn-cv" type="button" onClick={onDownload}>
        Download CV <Download size={16} />
      </button>
    </aside>
  )
}

export function VCardShell({ profile, user, onDownload, children }) {
  return (
    <>
      <Decor />
      <div className="vcard-page">
        <VCardSide profile={profile} user={user} onDownload={onDownload} />
        <div className="vcard-main">
          <VCardNav username={user?.username} email={profile?.public_email} profile={profile} />
          {children}
        </div>
      </div>
    </>
  )
}

export function SectionTitle({ lead, accent }) {
  return (
    <h2 className="section-title">
      {lead} {accent ? <span>{accent}</span> : null}
    </h2>
  )
}
