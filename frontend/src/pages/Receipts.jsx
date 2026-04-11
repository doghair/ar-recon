import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { fmtMoney } from '../utils.js'
import EditModal from '../components/EditModal.jsx'

const EDIT_FIELDS = [
  { key: 'status', label: 'Status', type: 'select', options: ['Applied', 'Unapplied'] },
  { key: 'invoice_id_applied', label: 'Applied To Invoice', type: 'text' },
  { key: 'payment_method', label: 'Payment Method', type: 'text' },
  { key: 'reference', label: 'Reference', type: 'text' },
]

export default function Receipts() {
  const [rows, setRows] = useState([])
  const [status, setStatus] = useState('')
  const [editing, setEditing] = useState(null)

  useEffect(() => {
    api.receipts({ status, limit: 1000 }).then(setRows)
  }, [status])

  async function handleSave(updated) {
    const changed = {}
    EDIT_FIELDS.forEach(f => {
      if (updated[f.key] !== editing[f.key]) changed[f.key] = updated[f.key]
    })
    if (Object.keys(changed).length === 0) return
    await api.updateReceipt(editing.receipt_id, changed)
    setRows(rs => rs.map(r => r.receipt_id === editing.receipt_id ? { ...r, ...changed } : r))
  }

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
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr><td colSpan={10} className="empty">No receipts found.</td></tr>
            )}
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
                <td>
                  <button className="btn-edit" onClick={() => setEditing(r)}>Edit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <EditModal
          title={`Edit Receipt ${editing.receipt_id}`}
          fields={EDIT_FIELDS}
          values={editing}
          onSave={handleSave}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  )
}
