import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Button, Card, ErrorText, Field } from '../components/ui'

export function AuthPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const [form, setForm] = useState({ email: '', password: '' })

  function update(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    setPending(true)
    try {
      await login(form.email, form.password)
      const next = location.state?.from?.pathname || '/app'
      navigate(next, { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="auth-wrap">
      <Card className="auth-card">
        <h1>Admin sign in</h1>
        <p className="muted">This portfolio has a single owner. Visitors use the public contact form instead of creating an account.</p>
        <form className="stack" style={{ marginTop: 18 }} onSubmit={submit}>
          <Field label="Email or username">
            <input
              type="text"
              name="email"
              value={form.email}
              onChange={update}
              required
              autoComplete="username"
              autoCapitalize="none"
            />
          </Field>
          <Field label="Password">
            <input type="password" name="password" value={form.password} onChange={update} minLength={8} required />
          </Field>
          <ErrorText error={error} />
          <Button type="submit" disabled={pending}>{pending ? 'Please wait…' : 'Sign in'}</Button>
        </form>
        <p style={{ marginTop: 16 }}>
          <Link to="/#contact">Back to contact</Link>
        </p>
      </Card>
    </div>
  )
}
