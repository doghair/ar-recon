export const fmtMoney = (n) => {
  if (n === null || n === undefined || n === '') return '—'
  const num = Number(n)
  if (Number.isNaN(num)) return '—'
  return '$' + num.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

// Compact smart-rounded format: $20.27M, $536k, $1.2k, $842.50
export const fmtMoneyCompact = (n) => {
  if (n === null || n === undefined || n === '') return '—'
  const num = Number(n)
  if (Number.isNaN(num)) return '—'
  const abs  = Math.abs(num)
  const sign = num < 0 ? '-' : ''
  if (abs >= 1_000_000_000) return `${sign}$${(abs / 1_000_000_000).toFixed(1)}B`
  if (abs >= 1_000_000)     return `${sign}$${(abs / 1_000_000).toFixed(1)}M`
  if (abs >= 10_000)        return `${sign}$${Math.round(abs / 1_000)}k`
  if (abs >= 1_000)         return `${sign}$${(abs / 1_000).toFixed(1)}k`
  return `${sign}$${abs.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export const fmtNum = (n) => {
  if (n === null || n === undefined || n === '') return '—'
  return Number(n).toLocaleString('en-US')
}

export const fmtDate = (s) => {
  if (!s) return '—'
  return s
}

export const varianceClass = (v) => {
  if (v === null || v === undefined) return 'zero'
  const n = Number(v)
  if (Math.abs(n) < 0.01) return 'zero'
  return n < 0 ? 'neg' : 'pos'
}

/**
 * Export an array of objects to a CSV file (Excel-compatible).
 * @param {Array<Object>} rows
 * @param {string} filename - without extension
 * @param {Array<{key: string, label: string}>} [columns] - optional column subset/order
 */
export function exportToCsv(rows, filename, columns) {
  if (!rows || rows.length === 0) return
  const cols = columns && columns.length
    ? columns
    : Object.keys(rows[0]).map(k => ({ key: k, label: k }))

  const esc = (v) => {
    if (v === null || v === undefined) return ''
    const s = String(v)
    return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }

  const header = cols.map(c => esc(c.label)).join(',')
  const body = rows.map(r => cols.map(c => esc(r[c.key])).join(',')).join('\r\n')
  // BOM so Excel opens UTF-8 cleanly
  const csv = '\ufeff' + header + '\r\n' + body

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${filename}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
