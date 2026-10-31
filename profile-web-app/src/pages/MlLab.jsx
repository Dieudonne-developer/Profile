import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Leaf, LineChart } from 'lucide-react'
import { api } from '../api'
import { Button, Card, Field } from '../components/ui'
import { PublicNav } from '../components/Layout'
import { useToast } from '../context/ToastContext'

export function MlLab() {
  const location = useLocation()
  const inApp = location.pathname.startsWith('/app')
  const toast = useToast()
  const [status, setStatus] = useState(null)
  const [hours, setHours] = useState(6)
  const [score, setScore] = useState(null)
  const [scoreBusy, setScoreBusy] = useState(false)
  const [leaf, setLeaf] = useState(null)
  const [preview, setPreview] = useState('')
  const [leafBusy, setLeafBusy] = useState(false)
  const [file, setFile] = useState(null)

  useEffect(() => {
    api('/api/ml/status').then(setStatus).catch(() => setStatus({ colab_connected: false }))
  }, [])

  async function runScore(event) {
    event.preventDefault()
    setScoreBusy(true)
    try {
      const result = await api('/api/ml/predict/score', {
        method: 'POST',
        body: JSON.stringify({ hours: Number(hours) }),
      })
      setScore(result)
    } catch (err) {
      toast.push(err.message, 'error')
    } finally {
      setScoreBusy(false)
    }
  }

  function onPick(event) {
    const next = event.target.files?.[0]
    setFile(next || null)
    setLeaf(null)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(next ? URL.createObjectURL(next) : '')
  }

  async function runLeaf(event) {
    event.preventDefault()
    if (!file) return toast.push('Choose a leaf photo first', 'error')
    setLeafBusy(true)
    try {
      const body = new FormData()
      body.append('file', file)
      const result = await api('/api/ml/predict/leaf', { method: 'POST', body })
      setLeaf(result)
    } catch (err) {
      toast.push(err.message, 'error')
    } finally {
      setLeafBusy(false)
    }
  }

  const connected = Boolean(status?.colab_connected)

  const page = (
    <div className="stack" style={inApp ? undefined : { maxWidth: 980, margin: '0 auto', padding: '24px 20px 64px' }}>
      <div className="page-title">
        <h1>Machine learning lab</h1>
        <p>
          Live demos from this portfolio: study-hours regression on FastAPI, and banana-leaf
          classification on Google Colab when the notebook server is running.
        </p>
      </div>

      <section className="card row space">
        <div>
          <span className={`status-pill ${connected ? 'on' : 'off'}`}>
            {connected ? 'Colab GPU connected' : 'Colab GPU not connected'}
          </span>
          <p className="muted" style={{ margin: '8px 0 0' }}>
            {connected
              ? `Leaf model classes: ${(status?.classes || []).join(', ')}`
              : 'Open notebooks/NTARINDWA_ML_Colab_Backend.ipynb in Colab, start the tunnel cell, then set ML_BACKEND_URL on the API.'}
          </p>
        </div>
        <Link className="btn btn-ghost" to="/u/dieudonne">
          Back to profile
        </Link>
      </section>

      <div className="grid grid-2">
        <Card>
          <div className="row" style={{ marginBottom: 8 }}>
            <LineChart size={22} />
            <h2 style={{ margin: 0 }}>Student score</h2>
          </div>
          <p className="muted">Ordinary least squares: examination score from weekly study hours.</p>
          <form className="stack" onSubmit={runScore}>
            <Field label={`Hours this week: ${hours}`}>
              <input
                type="range"
                min="0"
                max="16"
                step="0.5"
                value={hours}
                onChange={(event) => setHours(event.target.value)}
              />
            </Field>
            <Button type="submit" disabled={scoreBusy}>{scoreBusy ? 'Predicting…' : 'Predict score'}</Button>
          </form>
          {score ? (
            <div className="ml-result">
              <b>{score.predicted_score}</b>
              <span className="muted">/ 100 · {score.model}</span>
            </div>
          ) : null}
        </Card>

        <Card>
          <div className="row" style={{ marginBottom: 8 }}>
            <Leaf size={22} />
            <h2 style={{ margin: 0 }}>Banana leaf disease</h2>
          </div>
          <p className="muted">EfficientNet-B0 on Colab: Cordana, Healthy, Pestalotiopsis, Sigatoka.</p>
          <form className="stack" onSubmit={runLeaf}>
            <label className="ml-drop">
              {preview ? <img src={preview} alt="Selected leaf" /> : <span>Drop or choose a leaf photo (max 5 MB)</span>}
              <input type="file" accept="image/*" onChange={onPick} />
            </label>
            <Button type="submit" disabled={leafBusy || !connected}>
              {leafBusy ? 'Classifying…' : 'Classify leaf'}
            </Button>
          </form>
          {leaf ? (
            <div className="ml-result">
              <b>{leaf.label}</b>
              <span className="muted">{Math.round((leaf.confidence || 0) * 100)}% · {leaf.backend}</span>
              <div className="stack" style={{ marginTop: 10 }}>
                {Object.entries(leaf.probabilities || {}).map(([name, value]) => (
                  <div className="skill" key={name}>
                    <div className="row space">
                      <span>{name}</span>
                      <span>{Math.round(value * 100)}%</span>
                    </div>
                    <div className="skill-bar"><span style={{ width: `${Math.round(value * 100)}%` }} /></div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </Card>
      </div>
    </div>
  )

  if (inApp) return page
  return (
    <div>
      <PublicNav />
      {page}
    </div>
  )
}
