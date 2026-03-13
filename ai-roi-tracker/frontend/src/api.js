// In production, API is served from the same origin (no /api prefix needed)
// In dev, Vite proxies /api → localhost:8000
const BASE = import.meta.env.PROD ? '' : '/api'

export async function getSummary(days = 30, source = '', department = '') {
  const params = new URLSearchParams({ days })
  if (source) params.set('source', source)
  if (department) params.set('department', department)
  const res = await fetch(`${BASE}/metrics/summary?${params}`)
  return res.json()
}

export async function getDaily(days = 30) {
  const res = await fetch(`${BASE}/metrics/daily?days=${days}`)
  return res.json()
}

export async function getByDepartment(days = 30) {
  const res = await fetch(`${BASE}/metrics/by-department?days=${days}`)
  return res.json()
}

export async function getByTaskType(days = 30) {
  const res = await fetch(`${BASE}/metrics/by-task-type?days=${days}`)
  return res.json()
}

export async function getEvents(params = {}) {
  const p = new URLSearchParams(params)
  const res = await fetch(`${BASE}/events?${p}`)
  return res.json()
}

export async function logEvent(event) {
  const res = await fetch(`${BASE}/events/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event),
  })
  return res.json()
}

export async function syncOpenAI(apiKey) {
  const res = await fetch(`${BASE}/integrations/openai/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey }),
  })
  return res.json()
}

export async function syncAnthropic(apiKey) {
  const res = await fetch(`${BASE}/integrations/anthropic/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey }),
  })
  return res.json()
}

export async function syncCopilot(token, org) {
  const res = await fetch(`${BASE}/integrations/copilot/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: token, org }),
  })
  return res.json()
}
