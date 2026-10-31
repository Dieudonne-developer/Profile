import { useEffect, useState } from 'react'
import { api } from '../api'
import { useToast } from '../context/ToastContext'
import { Card } from '../components/ui'

export function Analytics() {
  const toast = useToast()
  const [stats, setStats] = useState(null)

  useEffect(() => {
    api('/api/analytics/summary').then(setStats).catch((err) => toast.push(err.message, 'error'))
  }, [toast])

  if (!stats) return <p>Loading analytics…</p>
  const max = Math.max(1, ...stats.last_14_days.map((d) => d.count))

  return (
    <div className="stack">
      <div className="page-title">
        <h1>Analytics</h1>
        <p>Last 30 days of profile activity, with a 14-day visit sparkline.</p>
      </div>
      <section className="grid stats-row">
        {[
          ['Total events', stats.total],
          ['Unique visitors', stats.unique_visitors],
          ['Profile views', stats.profile_views],
          ['CV downloads', stats.cv_downloads],
          ['Shares', stats.shares],
        ].map(([label, value]) => (
          <div className="stat" key={label}>
            <span className="muted">{label}</span>
            <b>{value}</b>
          </div>
        ))}
      </section>
      <Card>
        <h2>Last 14 days</h2>
        <div className="chart" aria-label="Visit counts">
          {stats.last_14_days.map((day) => (
            <i key={day.date} title={`${day.date}: ${day.count}`} style={{ height: `${(day.count / max) * 100}%` }} />
          ))}
        </div>
      </Card>
    </div>
  )
}
