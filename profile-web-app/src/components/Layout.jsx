import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  Bell,
  BrainCircuit,
  ChartColumn,
  FolderKanban,
  House,
  LogOut,
  Menu,
  Sparkles,
  UserRound,
  Users,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { api, mediaUrl, photoFallback } from '../api'

const links = [
  { to: '/app', label: 'Overview', icon: House, end: true },
  { to: '/app/profile', label: 'Edit profile', icon: UserRound },
  { to: '/app/projects', label: 'Projects', icon: FolderKanban },
  { to: '/app/network', label: 'Network', icon: Users },
  { to: '/app/feed', label: 'Project feed', icon: Sparkles },
  { to: '/app/notifications', label: 'Notifications', icon: Bell },
  { to: '/app/analytics', label: 'Analytics', icon: ChartColumn },
  { to: '/app/ml', label: 'ML lab', icon: BrainCircuit },
]

export function Layout() {
  const { user, profile, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    api('/api/notifications/unread-count')
      .then((data) => setUnread(data.count || 0))
      .catch(() => {})
  }, [location.pathname])

  return (
    <div className="app-shell">
      <div className={`sidebar-backdrop ${open ? 'open' : ''}`} onClick={() => setOpen(false)} />
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <NavLink to="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-mark">D</span>
          <span>
            NTARINDWA
            <small>ML Engineer</small>
          </span>
        </NavLink>
        <nav className="nav-links">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              onClick={() => setOpen(false)}
            >
              <link.icon size={18} />
              {link.label}
              {link.to === '/app/notifications' && unread ? <span className="nav-count">{unread}</span> : null}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="user-chip">
            <img src={mediaUrl(profile?.photo_path)} alt="" onError={photoFallback} />
            <div>
              <strong>{profile?.full_name || user?.username}</strong>
              <span>{user?.email}</span>
            </div>
          </div>
          <div className="nav-links" style={{ marginTop: 10 }}>
            {user ? (
              <NavLink to={`/u/${user.username}`} onClick={() => setOpen(false)}>
                Public profile
              </NavLink>
            ) : null}
            <button
              type="button"
              onClick={() => {
                logout()
                navigate('/')
              }}
            >
              <LogOut size={18} /> Sign out
            </button>
          </div>
        </div>
      </aside>
      <div className="main">
        <div className="topbar">
          <button className="menu-btn" type="button" onClick={() => setOpen((v) => !v)}>
            <Menu size={18} /> Menu
          </button>
        </div>
        <Outlet />
      </div>
    </div>
  )
}

export function PublicNav() {
  const { user } = useAuth()
  return (
    <header className="landing-nav">
      <NavLink to="/" className="brand">
        <span className="brand-mark">D</span>
        <span>
          NTARINDWA
          <small>ML Engineer</small>
        </span>
      </NavLink>
      <div className="row">
        {user ? (
          <NavLink className="btn btn-primary" to="/app">
            Dashboard
          </NavLink>
        ) : (
          <>
            <NavLink className="btn btn-ghost" to="/login">
              Sign in
            </NavLink>
            <NavLink className="btn btn-primary" to="/register">
              Create account
            </NavLink>
          </>
        )}
      </div>
    </header>
  )
}
