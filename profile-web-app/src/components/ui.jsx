import { mediaUrl } from '../api'

export function Card({ children, className = '' }) {
  return <section className={`card ${className}`}>{children}</section>
}

export function Button({ children, variant = 'primary', className = '', ...props }) {
  return (
    <button className={`btn btn-${variant} ${className}`} {...props}>
      {children}
    </button>
  )
}

export function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  )
}

export function Avatar({ src, alt, size = '' }) {
  return <img className={`avatar ${size}`} src={mediaUrl(src)} alt={alt || ''} />
}

export function Empty({ title, text }) {
  return (
    <div className="empty">
      <strong>{title}</strong>
      {text ? <p>{text}</p> : null}
    </div>
  )
}

export function ErrorText({ error }) {
  if (!error) return null
  return <p className="notice">{error}</p>
}
