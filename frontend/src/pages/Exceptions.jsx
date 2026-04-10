import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api.js'
import { fmtMoney, fmtNum, exportToCsv } from '../utils.js'

const CATEGORIES = [
  'Missing GL',
  'Duplicate GL',
  'Unapplied Cash',
  'Unapplied Credit',
  'Short Pay',
  'Timing Diff',
  'Write-Off Mismatch',
]

export default function Exceptions() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialCat = searchParams.get('category') || CATEGORIES[0]
  const [active, setActive] = useState(initialCat)
  const [rows, setRows] = useState([])
  const [counts, setCounts] = useState({})
  const [loading, setLoading] = useState(false)
  const [resolved, setResolved] = useState({})

  useEffect(() => {
    api.exceptions().then(all => {
      const c = {}
      for (const r of all) c[r.category] = (c[r.category] || 0) + 1
      setCounts(c)
    })
    // Load already-resolved items
    api.reconItems({}).then(items => {
      const m = {}
      for (const it of items) {
        if (it.status === 'Resolved' || it.status === 'Written Off') {
          m[`${it.category}::${it.entity_id}`] = it.status
        }
      }
      setResolved(m)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    api.exceptionDetail(active)
      .then(setRows)
      .catch(() => setRows([]))
      .finally(() => setLoading(false))
    setSearchParams({ category: active }, { replace: true })
  }, [active])

  const handleResolve = async (category, entityId, customerId, amount, action) => {
    const notes = prompt(`Resolution notes for ${entityId}:`)
    if (notes === null) return
    await api.resolveException({
      category,
      entity_id: entityId,
      customer_id: customerId,
      amount,
      resolution_notes: notes,
      status: action,
    })
    setResolved(prev => ({ ...prev, [`${category}::${entityId}`]: action }))
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Exception Queue</h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <span className="muted">Reconciling items requiring review</span>
          <button
            className="btn btn-sm"
            onClick={() => exportToCsv(rows, `exceptions_${active.replace(/\s/g, '_')}`)}
          >
            &#8615; Export
          </button>
        </div>
      </div>

      <div className="tabs">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            className={active === cat ? 'active' : ''}
            onClick={() => setActive(cat)}
          >
            {cat}
            <span className="count">{counts[cat] || 0}</span>
          </button>
        ))}
      </div>

      <div className="card">
        {loading && <div className="loading">Loading...</div>}
        {!loading && rows.length === 0 && <div className="empty">No exceptions in this category.</div>}
        {!loading && rows.length > 0 && (
          <ExceptionTable
            category={active}
            rows={rows}
            resolved={resolved}
            onResolve={handleResolve}
          />
        )}
      </div>

      {active === 'Unapplied Cash' && !loading && rows.length > 0 && (
        <MatchPanel rows={rows} />
      )}
    </div>
  )
}

function ResolveButtons({ category, entityId, customerId, amount, resolved, onResolve }) {
  const key = `${category}::${entityId}`
  if (resolved[key]) {
    return <span className={`badge ${resolved[key] === 'Resolved' ? 'paid' : 'writeoff'}`}>{resolved[key]}</span>
  }
  return (
    <div style={{ display: 'flex', gap: 4 }}>
      <button
        className="btn btn-xs btn-primary"
        onClick={() => onResolve(category, entityId, customerId, amount, 'Resolved')}
      >
        Resolve
      </button>
      <button
        className="btn btn-xs btn-danger"
        onClick={() => onResolve(category, entityId, customerId, amount, 'Written Off')}
      >
        Write Off
      </button>
    </div>
  )
}

function ExceptionTable({ category, rows, resolved, onResolve }) {
  const resolveCol = (entityId, customerId, amount) => (
    <ResolveButtons
      category={category}
      entityId={entityId}
      customerId={customerId}
      amount={amount}
      resolved={resolved}
      onResolve={onResolve}
    />
  )

  if (category === 'Missing GL') {
    return (
      <table className="table">
        <thead><tr>
          <th>Invoice ID</th><th>Customer</th><th>Date</th>
          <th className="right">Amount</th><th>Description</th><th>Action</th>
        </tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{r.invoice_id}</td>
              <td>{r.customer_name}</td>
              <td>{r.invoice_date}</td>
              <td className="right">{fmtMoney(r.amount)}</td>
              <td className="muted">{r.description}</td>
              <td>{resolveCol(r.invoice_id, r.customer_id, r.amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    )
  }
  if (category === 'Duplicate GL') {
    return (
      <table className="table">
        <thead><tr>
          <th>Invoice ID</th><th>Customer</th>
          <th className="right">Posts</th><th className="right">Total Debit</th>
          <th>Description</th><th>Action</th>
        </tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{r.invoice_id}</td>
              <td>{r.customer_id}</td>
              <td className="right text-neg">{r.gl_post_count}</td>
              <td className="right">{fmtMoney(r.total_debit_posted)}</td>
              <td className="muted">{r.description}</td>
              <td>{resolveCol(r.invoice_id, r.customer_id, r.total_debit_posted)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    )
  }
  if (category === 'Unapplied Cash') {
    return (
      <table className="table">
        <thead><tr>
          <th>Receipt ID</th><th>Customer</th><th>Date</th>
          <th>Method</th><th>Deposit</th><th className="right">Amount</th><th>Action</th>
        </tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{r.receipt_id}</td>
              <td>{r.customer_name}</td>
              <td>{r.receipt_date}</td>
              <td>{r.payment_method}</td>
              <td className="muted">{r.bank_deposit_id}</td>
              <td className="right">{fmtMoney(r.amount)}</td>
              <td>{resolveCol(r.receipt_id, r.customer_id, r.amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    )
  }
  if (category === 'Unapplied Credit') {
    return (
      <table className="table">
        <thead><tr>
          <th>Memo ID</th><th>Customer</th><th>Date</th>
          <th>Reason</th><th className="right">Amount</th><th>Action</th>
        </tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{r.memo_id}</td>
              <td>{r.customer_name}</td>
              <td>{r.memo_date}</td>
              <td>{r.reason}</td>
              <td className="right">{fmtMoney(r.amount)}</td>
              <td>{resolveCol(r.memo_id, r.customer_id, r.amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    )
  }
  if (category === 'Short Pay') {
    return (
      <table className="table">
        <thead><tr>
          <th>Invoice ID</th><th>Customer</th><th>Date</th>
          <th className="right">Invoiced</th><th className="right">Paid</th>
          <th className="right">Short By</th><th>Action</th>
        </tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{r.invoice_id}</td>
              <td>{r.customer_name}</td>
              <td>{r.invoice_date}</td>
              <td className="right">{fmtMoney(r.invoice_amount)}</td>
              <td className="right">{fmtMoney(r.paid_amount)}</td>
              <td className="right text-neg">{fmtMoney(r.short_paid_by)}</td>
              <td>{resolveCol(r.invoice_id, r.customer_id, r.short_paid_by)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    )
  }
  if (category === 'Timing Diff') {
    return (
      <table className="table">
        <thead><tr>
          <th>Line ID</th><th>Bank Date</th><th>Value Date</th>
          <th>Deposit</th><th className="right">Lag (days)</th>
          <th className="right">Amount</th><th>Action</th>
        </tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{r.line_id}</td>
              <td>{r.bank_date}</td>
              <td>{r.value_date}</td>
              <td>{r.deposit_id}</td>
              <td className="right text-warn">{r.lag_days}</td>
              <td className="right">{fmtMoney(r.amount)}</td>
              <td>{resolveCol(r.line_id, null, r.amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    )
  }
  if (category === 'Write-Off Mismatch') {
    return (
      <table className="table">
        <thead><tr>
          <th>Invoice ID</th><th>Customer</th><th>Entry Date</th>
          <th>Subledger Status</th><th className="right">Amount</th><th>Action</th>
        </tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{r.invoice_id}</td>
              <td>{r.customer_id}</td>
              <td>{r.entry_date}</td>
              <td><span className="badge writeoff">{r.subledger_status}</span></td>
              <td className="right">{fmtMoney(r.amount)}</td>
              <td>{resolveCol(r.invoice_id, r.customer_id, r.amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    )
  }
  return <pre>{JSON.stringify(rows, null, 2)}</pre>
}

/* ── Match Panel: suggests invoice matches for unapplied cash ─────────── */
function MatchPanel({ rows }) {
  const [selectedReceipt, setSelectedReceipt] = useState(null)
  const [matches, setMatches] = useState(null)
  const [matching, setMatching] = useState(false)
  const [applied, setApplied] = useState({})

  const findMatches = async (receiptId) => {
    setSelectedReceipt(receiptId)
    setMatching(true)
    try {
      const result = await api.matchSuggestions(receiptId)
      setMatches(result)
    } catch (e) {
      setMatches({ error: e.message })
    } finally {
      setMatching(false)
    }
  }

  const applyMatch = async (receiptId, invoiceId) => {
    if (!confirm(`Apply receipt ${receiptId} to invoice ${invoiceId}?`)) return
    try {
      await api.applyMatch(receiptId, invoiceId)
      setApplied(prev => ({ ...prev, [receiptId]: invoiceId }))
    } catch (e) {
      alert('Error: ' + e.message)
    }
  }

  return (
    <div className="card" style={{ marginTop: 20 }}>
      <div className="card-header">
        <h2>Match Engine</h2>
        <div className="muted">Select a receipt to find matching open invoices</div>
      </div>

      <div className="filters">
        <label>Receipt:
          <select
            value={selectedReceipt || ''}
            onChange={e => e.target.value && findMatches(e.target.value)}
          >
            <option value="">Select a receipt...</option>
            {rows.map(r => (
              <option key={r.receipt_id} value={r.receipt_id} disabled={!!applied[r.receipt_id]}>
                {r.receipt_id} — {r.customer_name} — {fmtMoney(r.amount)}
                {applied[r.receipt_id] ? ' (Applied)' : ''}
              </option>
            ))}
          </select>
        </label>
      </div>

      {matching && <div className="loading">Searching for matches...</div>}

      {matches && !matching && !matches.error && (
        <div>
          {matches.same_customer.length > 0 ? (
            <>
              <h3 style={{ fontSize: 13, color: 'var(--color-muted)', margin: '12px 0 8px' }}>
                Same Customer Matches
              </h3>
              <table className="table">
                <thead>
                  <tr>
                    <th>Invoice</th>
                    <th>Customer</th>
                    <th>Date</th>
                    <th className="right">Invoice Amt</th>
                    <th className="right">Diff</th>
                    <th className="center">Confidence</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {matches.same_customer.map(m => (
                    <tr key={m.invoice_id}>
                      <td>{m.invoice_id}</td>
                      <td>{m.customer_name}</td>
                      <td>{m.invoice_date}</td>
                      <td className="right">{fmtMoney(m.total_amount)}</td>
                      <td className="right">{fmtMoney(m.amount_diff)}</td>
                      <td className="center">
                        <span className={`badge ${m.confidence >= 90 ? 'paid' : m.confidence >= 60 ? 'open' : 'shortpay'}`}>
                          {m.confidence}%
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-xs btn-primary"
                          disabled={!!applied[selectedReceipt]}
                          onClick={() => applyMatch(selectedReceipt, m.invoice_id)}
                        >
                          Apply
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <div className="empty">No matching invoices found for this customer within tolerance.</div>
          )}

          {matches.cross_customer.length > 0 && (
            <>
              <h3 style={{ fontSize: 13, color: 'var(--color-muted)', margin: '12px 0 8px' }}>
                Cross-Customer Matches (exact amount)
              </h3>
              <table className="table">
                <thead>
                  <tr>
                    <th>Invoice</th>
                    <th>Customer</th>
                    <th>Date</th>
                    <th className="right">Amount</th>
                    <th className="center">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {matches.cross_customer.map(m => (
                    <tr key={m.invoice_id}>
                      <td>{m.invoice_id}</td>
                      <td>{m.customer_name}</td>
                      <td>{m.invoice_date}</td>
                      <td className="right">{fmtMoney(m.total_amount)}</td>
                      <td className="center">
                        <span className="badge shortpay">{m.confidence}%</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

      {matches && matches.error && (
        <div className="empty">Error: {matches.error}</div>
      )}
    </div>
  )
}
