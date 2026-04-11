import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { fmtMoney } from '../utils.js'

export default function BankStatements() {
  const [rows, setRows] = useState([])
  const [reconciled, setReconciled] = useState('')
  const [txnType, setTxnType] = useState('')

  useEffect(() => {
    api.bankStatements({ reconciled, transaction_type: txnType, limit: 1000 }).then(setRows)
  }, [reconciled, txnType])

  return (
    <div className="page">
      <div className="page-header">
        <h1>Bank Statements</h1>
        <div className="muted">{rows.length} lines</div>
      </div>

      <div className="filters">
        <label>Reconciled:
          <select value={reconciled} onChange={e => setReconciled(e.target.value)}>
            <option value="">All</option>
            <option value="Yes">Yes</option>
            <option value="No">No</option>
          </select>
        </label>
        <label>Type:
          <select value={txnType} onChange={e => setTxnType(e.target.value)}>
            <option value="">All</option>
            <option value="Deposit">Deposit</option>
            <option value="Bank Fee">Bank Fee</option>
            <option value="Wire Fee">Wire Fee</option>
          </select>
        </label>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Line ID</th>
              <th>Bank Date</th>
              <th>Value Date</th>
              <th>Description</th>
              <th>Type</th>
              <th className="right">Debit</th>
              <th className="right">Credit</th>
              <th>Deposit</th>
              <th>Reconciled</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr><td colSpan={9} className="empty">No bank statements found.</td></tr>
            )}
            {rows.map(r => (
              <tr key={r.line_id}>
                <td>{r.line_id}</td>
                <td>{r.bank_date}</td>
                <td>{r.value_date}</td>
                <td className="muted">{r.description}</td>
                <td>{r.transaction_type}</td>
                <td className="right">{r.debit > 0 ? fmtMoney(r.debit) : ''}</td>
                <td className="right">{r.credit > 0 ? fmtMoney(r.credit) : ''}</td>
                <td className="muted">{r.deposit_id}</td>
                <td>
                  <span className={`badge ${r.reconciled === 'Yes' ? 'applied' : 'unapplied'}`}>
                    {r.reconciled}
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
