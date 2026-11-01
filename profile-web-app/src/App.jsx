import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Landing } from './pages/Landing'
import { AuthPage } from './pages/Auth'
import { Dashboard } from './pages/Dashboard'
import { Editor } from './pages/Editor'
import { ProjectsPage } from './pages/ProjectsPage'
import { Feed } from './pages/Feed'
import { Network } from './pages/Network'
import { Notifications } from './pages/Notifications'
import { Analytics } from './pages/Analytics'
import { PublicProfile } from './pages/PublicProfile'
import { MlLab } from './pages/MlLab'
import { Messages } from './pages/Messages'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<AuthPage />} />
      <Route path="/register" element={<Navigate to="/" replace />} />
      <Route path="/u/:username" element={<PublicProfile />} />
      <Route path="/s/:token" element={<PublicProfile share />} />
      <Route path="/lab" element={<MlLab />} />
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="profile" element={<Editor />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="feed" element={<Feed />} />
        <Route path="network" element={<Network />} />
        <Route path="notifications" element={<Notifications />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="ml" element={<MlLab />} />
        <Route path="messages" element={<Messages />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
