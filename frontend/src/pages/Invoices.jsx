import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api.js'
import { fmtMoney, exportToCsv } from '../utils.js'

const STATUSES = ['', 'Open', 'Paid', 'Short Pay - Open', 'Written Off']

function statusBadge(s) {
  const cls = s === 'Paid'               ? 'paid'
           : s === 'Open'               ? 'open'
           : s === 'Short Pay - Open'   ? 'shortpay'
           : s === 'Written Off'        ? 'writeoff'
           : 'open'
  return <span className={`badge ${cls}`}>{s}</span>
}

export default function Invoices() {
  const [searchParams] = useSearchParams()
  const [rows, setRows] = useState([])
  const [status, setStatus] = useState(searchParams.get('status') || '')
  const [period, setPeriod] = useState('')

  useEffect(() => {
    api.invoices({ status, period, limit: 1000 }).then(setRows)
  }, [status, period])

  return (
    <div className="page">
      <div className="page-header">
        <h1>Invoices</h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <span className="muted">{rows.length} invoices</span>
          <button className="btn btn-sm" onClick={() => exportToCsv(rows, 'invoices')}>
            &#8615; Export
          </button>
        </div>
      </div>

      <div className="filters">
        <label>Status:
          <select value={status} onChange={e => setStatus(e.target.value)}>
            {STATUSES.map(s => <option key={s} value={s}>{s || 'All'}</option>)}
          </select>
        </label>
        <label>Period:
          <select value={period} onChange={e => setPeriod(e.target.value)}>
            <option value="">All</option>
            <option value="2026-01">2026-01</option>
            <option value="2026-02">2026-02</option>
            <option value="2026-03">2026-03</option>
          </select>
        </label>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Customer</th>
              <th>Date</th>
              <th>Due</th>
              <th>Product</th>
              <th className="right">Qty</th>
              <th className="right">Total</th>
              <th>Status</th>
              <th>GL Entry</th>
              <th>PO #</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.invoice_id}>
                <td>{r.invoice_id}</td>
                <td>{r.customer_id}</td>
                <td>{r.invoice_date}</td>
                <td>{r.due_date}</td>
                <td>{r.product_description}</td>
                <td className="right">{r.quantity}</td>
                <td className="right">{fmtMoney(r.total_amount)}</td>
                <td>{statusBadge(r.status)}</td>
                <td className={r.gl_entry_id ? '' : 'text-neg'}>
                  {r.gl_entry_id || 'MISSING'}
                </td>
                <td className="muted">{r.po_number}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
