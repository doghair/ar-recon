// Thin fetch wrapper. Uses VITE_API_URL if set (points to backend), else proxies via vite.
const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, params) {
  const qs = params
    ? '?' + new URLSearchParams(
        Object.fromEntries(
          Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
        )
      ).toString()
    : ''
  const res = await fetch(`${BASE}${path}${qs}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json()
}

async function patch(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json()
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json()
}

export const api = {
  health:             ()         => request('/api/health'),
  dashboard:          ()         => request('/api/dashboard'),
  kpis:               ()         => request('/api/kpis'),
  cashflow:           ()         => request('/api/cashflow'),
  arTrend:            ()         => request('/api/ar-trend'),
  arTrendDaily:       ()         => request('/api/ar-trend/daily'),
  reconCurrent:       ()         => request('/api/reconciliation/current'),
  reconByPeriod:      ()         => request('/api/reconciliation/by-period'),
  exceptions:         (category) => request('/api/exceptions', { category }),
  exceptionDetail:    (category) => request('/api/exceptions/detail', { category }),
  aging:              (params)   => request('/api/aging', params),
  agingSummary:       ()         => request('/api/aging/summary'),
  customers:          ()         => request('/api/customers'),
  customerBalances:   ()         => request('/api/customers/balances'),
  customerDetail:     (id)       => request(`/api/customers/${encodeURIComponent(id)}`),
  invoices:           (params)   => request('/api/invoices', params),
  receipts:           (params)   => request('/api/receipts', params),
  glEntries:          (params)   => request('/api/gl-entries', params),
  bankStatements:     (params)   => request('/api/bank-statements', params),

  // Period lock
  periods:            ()         => request('/api/periods'),
  lockPeriod:         (period)   => post(`/api/periods/${encodeURIComponent(period)}/lock`),
  unlockPeriod:       (period)   => post(`/api/periods/${encodeURIComponent(period)}/unlock`),

  // Match engine
  matchSuggestions:   (receiptId) => request(`/api/match/suggest/${encodeURIComponent(receiptId)}`),
  applyMatch:         (receiptId, invoiceId) => post('/api/match/apply', { receipt_id: receiptId, invoice_id: invoiceId }),

  // Inline edits
  updateInvoice:   (id, data) => patch(`/api/invoices/${encodeURIComponent(id)}`, data),
  updateReceipt:   (id, data) => patch(`/api/receipts/${encodeURIComponent(id)}`, data),
  updateCustomer:  (id, data) => patch(`/api/customers/${encodeURIComponent(id)}`, data),

  // Reconciliation items (manual resolution)
  reconItems:         (params)   => request('/api/reconciliation/items', params),
  resolveException:   (data)     => post('/api/reconciliation/items/resolve', data),
}
