import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { fmtMoney, fmtNum } from '../utils.js'

const BUCKETS = ['Current', '1-30', '31-60', '61-90', '91-120', '120+']

export default function Aging() {
  const [summary, setSummary] = useState([])
  const [rows, setRows] = useState([])
  const [bucket, setBucket] = useState('')

  useEffect(() => {
    api.agingSummary().then(setSummary)
  }, [])

  useEffect(() => {
    api.aging({ bucket }).then(setRows)
  }, [bucket])

  const totalAmount = summary.reduce((s, b) => s + (b.total || 0), 0)
  const totalCount  = summary.reduce((s, b) => s + b.count, 0)

  return (
    <div className="page">
      <div className="page-header">
        <h1>AR Aging Report</h1>
        <div className="muted">As of {new Date().toISOString().slice(0, 10)}</div>
      </div>

      {/* ── Bucket summary cards ───────────────────────────────────────── */}
      <div className="kpi-row" style={{ gridTemplateColumns: `repeat(${BUCKETS.length + 1}, 1fr)` }}>
        <div
          className="kpi-card"
          style={{ cursor: 'pointer', borderLeftColor: bucket === '' ? '#0ea5e9' : '#cbd5e1' }}
          onClick={() => setBucket('')}
        >
          <div className="kpi-label">Total</div>
          <div className="kpi-value" style={{ fontSize: 18 }}>{fmtMoney(totalAmount)}</div>
          <div className="kpi-sub">{fmtNum(totalCount)} invoices</div>
        </div>
        {BUCKETS.map(b => {
          const found = summary.find(s => s.aging_bucket === b)
          const isActive = bucket === b
          return (
            <div
              key={b}
              className="kpi-card"
              style={{
                cursor: 'pointer',
                borderLeftColor: isActive ? '#0ea5e9' : '#cbd5e1',
              }}
              onClick={() => setBucket(b)}
            >
              <div className="kpi-label">{b}</div>
              <div className="kpi-value" style={{ fontSize: 18 }}>
                {fmtMoney(found?.total || 0)}
              </div>
              <div className="kpi-sub">{fmtNum(found?.count || 0)} invoices</div>
            </div>
          )
        })}
      </div>

      {/* ── Detail table ───────────────────────────────────────────────── */}
      <div className="card">
        <h2>
          {bucket ? `Aging Bucket: ${bucket}` : 'All Open Invoices'}
          <span className="muted" style={{ marginLeft: 12, fontWeight: 'normal', textTransform: 'none' }}>
            ({rows.length} invoices)
          </span>
        </h2>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Invoice</th>
                <th>Customer</th>
                <th>Inv Date</th>
                <th>Due Date</th>
                <th className="right">Days PD</th>
                <th>Bucket</th>
                <th className="right">Invoice Amt</th>
                <th className="right">Open Balance</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr><td colSpan={8} className="empty">No aging records found.</td></tr>
              )}
              {rows.map(r => (
                <tr key={r.invoice_id}>
                  <td>{r.invoice_id}</td>
                  <td>{r.customer_name}</td>
                  <td>{r.invoice_date}</td>
                  <td>{r.due_date}</td>
                  <td className={`right ${r.days_past_due > 0 ? 'text-neg' : ''}`}>
                    {r.days_past_due}
                  </td>
                  <td>{r.aging_bucket}</td>
                  <td className="right">{fmtMoney(r.invoice_amount)}</td>
                  <td className="right"><strong>{fmtMoney(r.open_balance)}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
