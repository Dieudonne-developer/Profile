const TOKEN_KEY = 'portfolio.token'
const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

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

export const mediaUrl = (path) => {
  if (!path) return '/avatar.jpg'
  if (path.startsWith('http')) return path
  if (path.startsWith('/media/')) return apiUrl(path)
  if (path.startsWith('/')) return path
  return apiUrl(`/media/${path}`)
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
