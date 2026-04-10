import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { fmtMoney, fmtNum, varianceClass } from '../utils.js'
import {
  CashFlowChart,
  NetARChangeChart,
  ARTrendChart,
  AgingDonut,
  ExceptionPie,
  TopCustomersBar,
} from '../components/charts.jsx'

export default function Dashboard() {
  const [dash,     setDash]     = useState(null)
  const [kpis,     setKpis]     = useState(null)
  const [cashflow, setCashflow] = useState(null)
  const [trend,    setTrend]    = useState(null)
  const [err,      setErr]      = useState(null)

  useEffect(() => {
    Promise.all([
      api.dashboard(),
      api.kpis(),
      api.cashflow(),
      api.arTrend(),
    ])
      .then(([d, k, cf, t]) => {
        setDash(d); setKpis(k); setCashflow(cf); setTrend(t)
      })
      .catch(e => setErr(e.message))
  }, [])

  if (err)  return <div className="loading">Error: {err}</div>
  if (!dash || !kpis || !cashflow || !trend)
    return <div className="loading">Loading dashboard…</div>

  const { current, exception_counts, aging, period_summary, top_customers } = dash
  const vClass = varianceClass(current?.variance)

  return (
    <div className="page">
      <div className="page-header">
        <h1>AR Reconciliation Dashboard</h1>
        <div className="muted">As of 2026-04-09 · Period Q1 2026</div>
      </div>

      {/* ── KPI Strip: 5 cards ────────────────────────────────────────── */}
      <div className="kpi-strip">
        <div className="kpi-card">
          <div className="kpi-label">GL AR Control</div>
          <div className="kpi-value">{fmtMoney(current?.gl_ar_total)}</div>
          <div className="kpi-sub">Account 1200</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Subledger Open</div>
          <div className="kpi-value">{fmtMoney(current?.subledger_open_total)}</div>
          <div className="kpi-sub">{fmtNum(kpis.open_invoice_count)} open invoices</div>
        </div>
        <div className={`kpi-card variance ${vClass}`}>
          <div className="kpi-label">Variance</div>
          <div className="kpi-value">{fmtMoney(current?.variance)}</div>
          <div className="kpi-sub">
            {vClass === 'zero' ? 'Fully Reconciled' : 'Needs Investigation'}
          </div>
        </div>
        <div className="kpi-card accent">
          <div className="kpi-label">Cash Collected</div>
          <div className="kpi-value">{fmtMoney(kpis.total_collected)}</div>
          <div className="kpi-sub">
            {kpis.collection_rate}% collection rate
          </div>
        </div>
        <div className="kpi-card accent">
          <div className="kpi-label">DSO</div>
          <div className="kpi-value" style={{ color: kpis.dso_days > 45 ? '#dc2626' : '#059669' }}>
            {kpis.dso_days} <span style={{ fontSize: 14, fontWeight: 500 }}>days</span>
          </div>
          <div className="kpi-sub">
            Avg invoice {fmtMoney(kpis.avg_invoice_size)}
          </div>
        </div>
      </div>

      {/* ── Cash Flow (hero chart) ────────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <h2>Cash Flow: Invoiced vs Collected</h2>
          <div className="muted">
            Invoiced {fmtMoney(kpis.total_invoiced)} ·
            Collected {fmtMoney(kpis.total_collected)} ·
            Credits {fmtMoney(kpis.total_credit_memos)} ·
            Write-Offs {fmtMoney(kpis.total_writeoffs)}
          </div>
        </div>
        <CashFlowChart data={cashflow} />
      </div>

      {/* ── AR Trend + Net AR Change ──────────────────────────────────── */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h2>AR Balance Trend</h2>
            <div className="muted">Running GL AR control account</div>
          </div>
          <ARTrendChart data={trend} />
        </div>
        <div className="card">
          <div className="card-header">
            <h2>Net AR Change</h2>
            <div className="muted">Monthly AR movement (invoiced − collections)</div>
          </div>
          <NetARChangeChart data={cashflow} />
        </div>
      </div>

      {/* ── Aging donut + Exception pie ───────────────────────────────── */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h2>AR Aging Distribution</h2>
            <Link to="/aging" className="muted">View detail →</Link>
          </div>
          <AgingDonut data={aging} />
        </div>
        <div className="card">
          <div className="card-header">
            <h2>Exception Breakdown</h2>
            <Link to="/exceptions" className="muted">View queue →</Link>
          </div>
          <ExceptionPie data={exception_counts} />
        </div>
      </div>

      {/* ── Top Customers Bar ─────────────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <h2>Top 10 Open Customer Balances</h2>
          <Link to="/invoices?status=Open" className="muted">View invoices →</Link>
        </div>
        <TopCustomersBar data={top_customers} />
      </div>

      {/* ── Exception Queue + Period Movement ─────────────────────────── */}
      <div className="grid-2">
        <div className="card">
          <h2>Exception Queue</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Category</th>
                <th className="right">Count</th>
                <th className="right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {exception_counts.map(e => (
                <tr key={e.category}>
                  <td>
                    <Link to={`/exceptions?category=${encodeURIComponent(e.category)}`}>
                      {e.category}
                    </Link>
                  </td>
                  <td className="right">{fmtNum(e.count)}</td>
                  <td className="right">{fmtMoney(e.total)}</td>
                </tr>
              ))}
              <tr style={{ fontWeight: 600, background: '#f8fafc' }}>
                <td>Total</td>
                <td className="right">
                  {fmtNum(exception_counts.reduce((s, e) => s + e.count, 0))}
                </td>
                <td className="right">
                  {fmtMoney(exception_counts.reduce((s, e) => s + (e.total || 0), 0))}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2>Period Movement: GL vs Subledger</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Period</th>
                <th className="right">GL Net</th>
                <th className="right">Subledger Net</th>
                <th className="right">Variance</th>
              </tr>
            </thead>
            <tbody>
              {period_summary.map(p => {
                const cls = varianceClass(p.variance)
                return (
                  <tr key={p.period}>
                    <td>{p.period}</td>
                    <td className="right">{fmtMoney(p.gl_net_movement)}</td>
                    <td className="right">{fmtMoney(p.subledger_net_movement)}</td>
                    <td className={`right ${cls === 'zero' ? '' : cls === 'neg' ? 'text-neg' : 'text-warn'}`}>
                      {fmtMoney(p.variance)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
