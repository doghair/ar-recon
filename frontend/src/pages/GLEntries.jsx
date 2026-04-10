import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { fmtMoney } from '../utils.js'

const ACCOUNTS = [
  ['',     'All Accounts'],
  ['1000', '1000 · Cash'],
  ['1200', '1200 · Accounts Receivable'],
  ['2050', '2050 · Customer Deposits – Suspense'],
  ['4000', '4000 · Revenue – Product Sales'],
  ['5500', '5500 · Bad Debt Expense'],
]

export default function GLEntries() {
  const [rows, setRows] = useState([])
  const [account, setAccount] = useState('1200')
  const [period, setPeriod] = useState('')

  useEffect(() => {
    api.glEntries({ account_code: account, period, limit: 1000 }).then(setRows)
  }, [account, period])

  const debits  = rows.reduce((s, r) => s + (r.debit || 0), 0)
  const credits = rows.reduce((s, r) => s + (r.credit || 0), 0)
  const net     = debits - credits

  return (
    <div className="page">
      <div className="page-header">
        <h1>General Ledger Entries</h1>
        <div className="muted">
          {rows.length} entries · Debits {fmtMoney(debits)} · Credits {fmtMoney(credits)} · Net {fmtMoney(net)}
        </div>
      </div>

      <div className="filters">
        <label>Account:
          <select value={account} onChange={e => setAccount(e.target.value)}>
            {ACCOUNTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label>Period:
          <select value={period} onChange={e => setPeriod(e.target.value)}>
            <option value="">All</option>
            <option value="2026-01">2026-01</option>
            <option value="2026-02">2026-02</option>
            <option value="2026-03">2026-03</option>
            <option value="2026-04">2026-04</option>
          </select>
        </label>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Entry ID</th>
              <th>Date</th>
              <th>Period</th>
              <th>Account</th>
              <th>Type</th>
              <th className="right">Debit</th>
              <th className="right">Credit</th>
              <th>Source</th>
              <th>Customer</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.entry_id}>
                <td>{r.entry_id}</td>
                <td>{r.entry_date}</td>
                <td>{r.period}</td>
                <td>{r.account_code} {r.account_name}</td>
                <td>{r.entry_type}</td>
                <td className="right">{r.debit > 0 ? fmtMoney(r.debit) : ''}</td>
                <td className="right">{r.credit > 0 ? fmtMoney(r.credit) : ''}</td>
                <td>{r.source_doc}</td>
                <td>{r.customer_id}</td>
                <td className="muted">{r.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
