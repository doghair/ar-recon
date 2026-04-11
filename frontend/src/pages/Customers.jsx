import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { fmtMoney, fmtNum, exportToCsv } from '../utils.js'

export default function Customers() {
  const [balances, setBalances] = useState([])
  const [search, setSearch] = useState('')

  useEffect(() => {
    api.customerBalances().then(setBalances)
  }, [])

  const filtered = balances.filter(c =>
    !search || c.customer_name.toLowerCase().includes(search.toLowerCase())
      || c.customer_id.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="page">
      <div className="page-header">
        <h1>Customer Balances</h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <span className="muted">{filtered.length} customers</span>
          <button
            className="btn btn-sm"
            onClick={() => exportToCsv(filtered, 'customer_balances', [
              { key: 'customer_id', label: 'Customer ID' },
              { key: 'customer_name', label: 'Customer Name' },
              { key: 'customer_type', label: 'Type' },
              { key: 'open_invoice_count', label: 'Open Invoices' },
              { key: 'gross_open', label: 'Gross Open' },
              { key: 'cash_applied', label: 'Cash Applied' },
              { key: 'credit_applied', label: 'Credits Applied' },
              { key: 'net_open_balance', label: 'Net Open Balance' },
            ])}
          >
            &#8615; Export
          </button>
        </div>
      </div>

      <div className="filters">
        <label>Search:
          <input
            type="text"
            placeholder="Customer name or ID…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ minWidth: 240 }}
          />
        </label>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Customer</th>
              <th>Type</th>
              <th className="right">Open Invoices</th>
              <th className="right">Gross Open</th>
              <th className="right">Cash Applied</th>
              <th className="right">Credits</th>
              <th className="right">Net Open</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr><td colSpan={8} className="empty">No customers found.</td></tr>
            )}
            {filtered.map(c => (
              <tr key={c.customer_id}>
                <td>
                  <Link to={`/customers/${c.customer_id}`}>
                    {c.customer_name}
                  </Link>
                </td>
                <td className="muted">{c.customer_type}</td>
                <td className="right">{fmtNum(c.open_invoice_count)}</td>
                <td className="right">{fmtMoney(c.gross_open)}</td>
                <td className="right">{fmtMoney(c.cash_applied)}</td>
                <td className="right">{fmtMoney(c.credit_applied)}</td>
                <td className="right" style={{ fontWeight: 600 }}>{fmtMoney(c.net_open_balance)}</td>
                <td>
                  <Link to={`/customers/${c.customer_id}`} className="muted">
                    View →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
