export function formatBirthday(value) {
  if (!value) return '01 January 2002'
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (match) {
    const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
    return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })
  }
  if (String(value).includes('/')) {
    const [day, month, year] = String(value).split('/')
    if (year && month && day) {
      const date = new Date(Number(year), Number(month) - 1, Number(day))
      if (!Number.isNaN(date.getTime())) {
        return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })
      }
    }
  }
  return String(value)
}

export function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
}

export function rangeLabel(start, end, current) {
  const from = formatDate(start) || start || ''
  const to = current ? 'Present' : formatDate(end) || end || ''
  return [from, to].filter(Boolean).join(' – ')
}

export function timeAgo(value) {
  if (!value) return ''
  const date = new Date(value)
  const diff = Date.now() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 14) return `${days}d ago`
  return date.toLocaleDateString()
}

export function groupBy(items, key) {
  return items.reduce((acc, item) => {
    const group = item[key] || 'General'
    acc[group] = acc[group] || []
    acc[group].push(item)
    return acc
  }, {})
}
