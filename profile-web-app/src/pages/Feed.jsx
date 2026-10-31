import { useEffect, useState } from 'react'
import { api } from '../api'
import { useToast } from '../context/ToastContext'
import { ProjectCard } from '../components/ProjectCard'
import { Empty } from '../components/ui'

export function Feed() {
  const toast = useToast()
  const [projects, setProjects] = useState([])

  useEffect(() => {
    api('/api/projects/feed').then(setProjects).catch((err) => toast.push(err.message, 'error'))
  }, [toast])

  return (
    <div className="stack">
      <div className="page-title">
        <h1>Project feed</h1>
        <p>Latest work published across the network.</p>
      </div>
      {projects.length ? projects.map((project) => (
        <ProjectCard
          key={project.id}
          project={project}
          onChange={(next) => setProjects((rows) => rows.map((row) => (row.id === next.id ? next : row)))}
        />
      )) : <Empty title="No projects yet" text="Publish a project to appear in the feed." />}
    </div>
  )
}
