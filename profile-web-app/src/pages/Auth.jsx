import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Button, Card, ErrorText, Field } from '../components/ui'

export function AuthPage({ mode }) {
  const isRegister = mode === 'register'
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const [form, setForm] = useState({
    email: isRegister ? '' : 'ntarindwajean11@gmail.com',
    username: '',
    full_name: '',
    password: isRegister ? '' : 'Portfolio2026!',
  })

  function update(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    setPending(true)
    try {
      if (isRegister) {
        await register({
          email: form.email,
          username: form.username,
          password: form.password,
          full_name: form.full_name,
        })
      } else {
        await login(form.email, form.password)
      }
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
        <h1>{isRegister ? 'Create your portfolio' : 'Welcome back'}</h1>
        <p className="muted">
          {isRegister
            ? 'Register to publish a public profile, projects, and a downloadable CV.'
            : 'Sign in to manage your profile, analytics, and network.'}
        </p>
        <form className="stack" style={{ marginTop: 18 }} onSubmit={submit}>
          {isRegister ? (
            <>
              <Field label="Full name">
                <input name="full_name" value={form.full_name} onChange={update} required />
              </Field>
              <Field label="Username">
                <input name="username" value={form.username} onChange={update} minLength={3} required />
              </Field>
            </>
          ) : null}
          <Field label="Email">
            <input type="email" name="email" value={form.email} onChange={update} required />
          </Field>
          <Field label="Password">
            <input type="password" name="password" value={form.password} onChange={update} minLength={8} required />
          </Field>
          <ErrorText error={error} />
          <Button type="submit" disabled={pending}>{pending ? 'Please wait…' : isRegister ? 'Create account' : 'Sign in'}</Button>
        </form>
        <p style={{ marginTop: 16 }}>
          {isRegister ? (
            <>Already have an account? <Link to="/login">Sign in</Link></>
          ) : (
            <>New here? <Link to="/register">Create an account</Link></>
          )}
        </p>
        {!isRegister ? (
          <p className="muted" style={{ marginTop: 8 }}>
            Owner login: ntarindwajean11@gmail.com / Portfolio2026!
          </p>
        ) : null}
      </Card>
    </div>
  )
}
