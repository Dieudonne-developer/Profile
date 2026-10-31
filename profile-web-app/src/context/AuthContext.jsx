import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api, getToken, setToken } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  async function refresh() {
    if (!getToken()) {
      setUser(null)
      setProfile(null)
      setLoading(false)
      return
    }
    try {
      const me = await api('/api/auth/me')
      const mine = await api('/api/profile/me')
      setUser(me)
      setProfile(mine)
    } catch {
      setToken(null)
      setUser(null)
      setProfile(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function login(email, password) {
    const token = await api('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    setToken(token.access_token)
    await refresh()
  }

  async function register(payload) {
    const token = await api('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    setToken(token.access_token)
    await refresh()
  }

  function logout() {
    setToken(null)
    setUser(null)
    setProfile(null)
  }

  const value = useMemo(
    () => ({ user, profile, loading, login, register, logout, refresh }),
    [user, profile, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
