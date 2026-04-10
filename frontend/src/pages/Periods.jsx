import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { fmtMoney, varianceClass } from '../utils.js'

export default function Periods() {
  const [periods, setPeriods] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.periods().then(setPeriods).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const lockPeriod = async (period) => {
    if (!confirm(`Lock period ${period}? This prevents further posting.`)) return
    await api.lockPeriod(period)
    load()
  }

  const unlockPeriod = async (period) => {
    if (!confirm(`Unlock period ${period}?`)) return
    await api.unlockPeriod(period)
    load()
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Period Management</h1>
        <div className="muted">Lock reconciled periods to prevent further changes</div>
      </div>

      {loading && <div className="loading">Loading…</div>}
      {!loading && (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Period</th>
                <th>Status</th>
                <th className="right">GL Balance</th>
                <th className="right">Subledger</th>
                <th className="right">Variance</th>
                <th>Reconciled By</th>
                <th>Locked At</th>
                <th className="center">Action</th>
              </tr>
            </thead>
            <tbody>
              {periods.map(p => {
                const vCls = varianceClass(p.variance)
                return (
                  <tr key={p.period}>
                    <td style={{ fontWeight: 600 }}>{p.period}</td>
                    <td>
                      <span className={`badge ${
                        p.status === 'Locked' ? 'writeoff'
                        : p.status === 'Reconciled' ? 'paid'
                        : 'open'
                      }`}>{p.status}</span>
                    </td>
                    <td className="right">{fmtMoney(p.gl_balance)}</td>
                    <td className="right">{fmtMoney(p.subledger_balance)}</td>
                    <td className={`right ${vCls === 'zero' ? 'text-pos' : 'text-neg'}`}>
                      {fmtMoney(p.variance)}
                    </td>
                    <td className="muted">{p.reconciled_by || '—'}</td>
                    <td className="muted">{p.locked_at || '—'}</td>
                    <td className="center">
                      {p.status === 'Locked' ? (
                        <button className="btn btn-sm btn-danger" onClick={() => unlockPeriod(p.period)}>
                          Unlock
                        </button>
                      ) : (
                        <button className="btn btn-sm btn-primary" onClick={() => lockPeriod(p.period)}>
                          Lock
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
