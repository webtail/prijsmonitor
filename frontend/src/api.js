const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) throw new Error(`API fout: ${res.status}`)
  return res.json()
}

export const api = {
  getProducten:      ()           => request('/producten'),
  voegProductToe:    (data)       => request('/producten', { method: 'POST', body: JSON.stringify(data) }),
  verwijderProduct:  (id)         => request(`/producten/${id}`, { method: 'DELETE' }),
  getPrijsHistoriek: (id)         => request(`/prijzen/${id}`),
  startScrape:       ()           => request('/scrape', { method: 'POST' }),
  getLaatsteScrape:  ()           => request('/laatste-scrape'),
  getEmails:         ()           => request('/emails'),
  voegEmailToe:      (email)      => request('/emails', { method: 'POST', body: JSON.stringify({ email }) }),
  verwijderEmail:    (email)      => request(`/emails/${encodeURIComponent(email)}`, { method: 'DELETE' }),
}
