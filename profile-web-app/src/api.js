const TOKEN_KEY = 'portfolio.token'
const PRODUCTION_API = 'https://profile-nine-lake-75.vercel.app'
const fromEnv = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
const stalePreview = fromEnv.includes('profile-qt8o8gs3x')
const API_BASE = (
  stalePreview ? PRODUCTION_API : fromEnv || (import.meta.env.PROD ? PRODUCTION_API : '')
).replace(/\/$/, '')

export function apiUrl(path) {
  if (!path) return API_BASE || '/'
  if (path.startsWith('http')) return path
  return `${API_BASE}${path}`
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (!(options.body instanceof FormData) && !headers['Content-Type'] && options.body) {
    headers['Content-Type'] = 'application/json'
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(apiUrl(path), { ...options, headers })
  if (response.status === 502 || response.status === 503) {
    const isJson = (response.headers.get('content-type') || '').includes('application/json')
    let detail = ''
    if (isJson) {
      try {
        const body = await response.clone().json()
        detail = body?.detail || ''
      } catch {
        detail = ''
      }
    }
    const error = new Error(
      detail ||
        'The API is not running. Start FastAPI on port 8000, or start the Colab notebook for GPU inference.',
    )
    error.status = response.status
    throw error
  }
  if (response.status === 204) return null
  const isJson = (response.headers.get('content-type') || '').includes('application/json')
  let data
  try {
    data = isJson ? await response.json() : await response.blob()
  } catch {
    if (!response.ok) {
      const error = new Error(response.statusText || 'Request failed')
      error.status = response.status
      throw error
    }
    throw new Error('The server returned an unexpected response.')
  }
  if (!response.ok) {
    const detail = data?.detail
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg || item.detail || JSON.stringify(item)).join(' ')
      : detail || response.statusText
    const error = new Error(message)
    error.status = response.status
    throw error
  }
  return data
}

export const FALLBACK_PHOTO = '/avatar.jpg'

export const mediaUrl = (path) => {
  if (!path) return FALLBACK_PHOTO
  if (path.startsWith('http')) return path
  if (path.startsWith('/media/')) return apiUrl(path)
  if (path.startsWith('/')) return path
  return apiUrl(`/media/${path}`)
}

export function photoFallback(event) {
  if (!event.currentTarget.src.endsWith(FALLBACK_PHOTO)) {
    event.currentTarget.src = FALLBACK_PHOTO
  }
}

export async function downloadCv(username) {
  const path = username ? `/api/cv/${username}` : '/api/cv/me'
  const blob = await api(path)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${username || 'profile'}-cv.pdf`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

const NOTIFY_EMAIL = (import.meta.env.VITE_NOTIFY_EMAIL || 'ntarindwajean11@gmail.com').trim()

export async function notifyOwnerEmail({ name, email, subject, message }) {
  const response = await fetch(`https://formsubmit.co/ajax/${encodeURIComponent(NOTIFY_EMAIL)}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      name,
      email,
      _replyto: email,
      _subject: `[Portfolio] ${subject || 'Portfolio contact'}`,
      message,
      _template: 'box',
      _captcha: 'false',
    }),
  })
  if (!response.ok) {
    throw new Error(`Gmail notify failed (${response.status})`)
  }
}

export function trackEvent(username, eventType, extra = {}) {
  if (!username) return
  api('/api/analytics/track', {
    method: 'POST',
    body: JSON.stringify({
      username,
      event_type: eventType,
      path: window.location.pathname,
      referrer: document.referrer,
      ...extra,
    }),
  }).catch(() => {})
}
