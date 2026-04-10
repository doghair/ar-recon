import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { fmtMoney } from '../utils.js'

export default function Receipts() {
  const [rows, setRows] = useState([])
  const [status, setStatus] = useState('')

  useEffect(() => {
    api.receipts({ status, limit: 1000 }).then(setRows)
  }, [status])

  return (
    <div className="page">
      <div className="page-header">
        <h1>Cash Receipts</h1>
        <div className="muted">{rows.length} receipts</div>
      </div>

      <div className="filters">
        <label>Status:
          <select value={status} onChange={e => setStatus(e.target.value)}>
            <option value="">All</option>
            <option value="Applied">Applied</option>
            <option value="Unapplied">Unapplied</option>
          </select>
        </label>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Receipt ID</th>
              <th>Customer</th>
              <th>Date</th>
              <th>Method</th>
              <th>Reference</th>
              <th>Applied To</th>
              <th className="right">Amount</th>
              <th>Deposit</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.receipt_id}>
                <td>{r.receipt_id}</td>
                <td>{r.customer_id}</td>
                <td>{r.receipt_date}</td>
                <td>{r.payment_method}</td>
                <td className="muted">{r.reference}</td>
                <td>{r.invoice_id_applied || '—'}</td>
                <td className="right">{fmtMoney(r.amount)}</td>
                <td className="muted">{r.bank_deposit_id}</td>
                <td>
                  <span className={`badge ${r.status === 'Applied' ? 'applied' : 'unapplied'}`}>
                    {r.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
