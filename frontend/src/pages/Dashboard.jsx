import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { fmtMoney, fmtMoneyCompact, fmtNum, varianceClass } from '../utils.js'
import {
  CashFlowChart,
  NetARChangeChart,
  ARTrendChart,
  AgingDonut,
  ExceptionPie,
  TopCustomersBar,
} from '../components/charts.jsx'

// ── Period helpers ────────────────────────────────────────────────────────────
const PRESETS = ['Q1', 'Q2', 'Q3', 'Q4', 'YTD', 'Custom']
const QUARTER_RANGES = {
  Q1: ['01-01', '03-31'],
  Q2: ['04-01', '06-30'],
  Q3: ['07-01', '09-30'],
  Q4: ['10-01', '12-31'],
}

function presetRange(preset, year) {
  const today = new Date().toISOString().slice(0, 10)
  if (preset === 'YTD') return [`${year}-01-01`, today]
  const [s, e] = QUARTER_RANGES[preset]
  return [`${year}-${s}`, `${year}-${e}`]
}

function fmtPresetLabel(preset, year) {
  if (preset === 'YTD') return `YTD ${year}`
  return `${preset} ${year}`
}

// ── Period selector component ─────────────────────────────────────────────────
function PeriodSelector({ preset, year, customFrom, customTo, onChange }) {
  const currentYear = new Date().getFullYear()
  const years = [currentYear - 1, currentYear, currentYear + 1]

  function setPreset(p) {
    if (p === 'Custom') { onChange({ preset: 'Custom', year, customFrom, customTo }); return }
    const [from, to] = presetRange(p, year)
    onChange({ preset: p, year, customFrom: from, customTo: to })
  }

  function setYear(y) {
    const newYear = Number(y)
    if (preset === 'Custom') { onChange({ preset, year: newYear, customFrom, customTo }); return }
    const [from, to] = presetRange(preset, newYear)
    onChange({ preset, year: newYear, customFrom: from, customTo: to })
  }

  function setCustom(field, val) {
    const next = { preset: 'Custom', year, customFrom, customTo, [field]: val }
    onChange(next)
  }

  return (
    <div className="period-selector">
      <div className="period-selector-row">
        <select
          className="period-year-select"
          value={year}
          onChange={e => setYear(e.target.value)}
        >
          {years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>

        <div className="period-presets">
          {PRESETS.map(p => (
            <button
              key={p}
              className={`period-btn${preset === p ? ' active' : ''}`}
              onClick={() => setPreset(p)}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {preset === 'Custom' && (
        <div className="period-custom">
          <label>
            From
            <input
              type="date"
              value={customFrom}
              onChange={e => setCustom('customFrom', e.target.value)}
            />
          </label>
          <span className="period-custom-sep">→</span>
          <label>
            To
            <input
              type="date"
              value={customTo}
              onChange={e => setCustom('customTo', e.target.value)}
            />
          </label>
        </div>
      )}
    </div>
  )
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
const TODAY = new Date().toISOString().slice(0, 10)
const CUR_YEAR = new Date().getFullYear()

export default function Dashboard() {
  const [dash,     setDash]     = useState(null)
  const [kpis,     setKpis]     = useState(null)
  const [cashflow, setCashflow] = useState(null)
  const [trend,    setTrend]    = useState(null)
  const [err,      setErr]      = useState(null)
  const [loading,  setLoading]  = useState(false)

  // Period state — default to Q1 of current year (where the data lives)
  const [period, setPeriod] = useState({
    preset:     'Q1',
    year:       CUR_YEAR,
    customFrom: `${CUR_YEAR}-01-01`,
    customTo:   `${CUR_YEAR}-03-31`,
  })

  // Load static dashboard data once (aging, exceptions, trend don't change with period)
  useEffect(() => {
    Promise.all([api.dashboard(), api.arTrend()])
      .then(([d, t]) => { setDash(d); setTrend(t) })
      .catch(e => setErr(e.message))
  }, [])

  // Reload KPIs + cashflow whenever period changes
  useEffect(() => {
    const params = { date_from: period.customFrom, date_to: period.customTo }
    setLoading(true)
    Promise.all([api.kpis(params), api.cashflow(params)])
      .then(([k, cf]) => { setKpis(k); setCashflow(cf) })
      .catch(e => setErr(e.message))
      .finally(() => setLoading(false))
  }, [period.customFrom, period.customTo])

  function handlePeriodChange(next) {
    // For custom, only refetch once both dates are set
    if (next.preset === 'Custom' && (!next.customFrom || !next.customTo)) {
      setPeriod(next)
      return
    }
    setPeriod(next)
  }

  if (err) return <div className="loading">Error: {err}</div>
  if (!dash || !trend) return <div className="loading">Loading dashboard…</div>

  const { current, exception_counts, aging, period_summary, top_customers } = dash
  const vClass = varianceClass(current?.variance)
  const periodLabel = period.preset === 'Custom'
    ? `${period.customFrom} → ${period.customTo}`
    : fmtPresetLabel(period.preset, period.year)

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>AR Reconciliation Dashboard</h1>
          <div className="muted" style={{ marginTop: 2 }}>
            {periodLabel} · As of {TODAY}
          </div>
        </div>
      </div>

      {/* ── Period Selector ───────────────────────────────────────────────── */}
      <PeriodSelector
        preset={period.preset}
        year={period.year}
        customFrom={period.customFrom}
        customTo={period.customTo}
        onChange={handlePeriodChange}
      />

      {/* ── KPI Strip: 5 cards ────────────────────────────────────────────── */}
      <div className={`kpi-strip${loading ? ' kpi-loading' : ''}`}>
        <div className="kpi-card">
          <div className="kpi-label">GL AR Control</div>
          <div className="kpi-value">{fmtMoneyCompact(current?.gl_ar_total)}</div>
          <div className="kpi-sub">Account 1200 · {fmtMoney(current?.gl_ar_total)}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Subledger Open</div>
          <div className="kpi-value">{fmtMoneyCompact(current?.subledger_open_total)}</div>
          <div className="kpi-sub">{fmtNum(kpis?.open_invoice_count ?? '—')} open invoices</div>
        </div>
        <div className={`kpi-card variance ${vClass}`}>
          <div className="kpi-label">Variance</div>
          <div className="kpi-value">{fmtMoneyCompact(current?.variance)}</div>
          <div className="kpi-sub">
            {vClass === 'zero' ? 'Fully Reconciled' : 'Needs Investigation'}
          </div>
        </div>
        <div className="kpi-card accent">
          <div className="kpi-label">Cash Collected</div>
          <div className="kpi-value">{fmtMoneyCompact(kpis?.total_collected)}</div>
          <div className="kpi-sub">
            {kpis?.collection_rate}% collection rate
          </div>
        </div>
        <div className="kpi-card accent">
          <div className="kpi-label">DSO</div>
          <div className="kpi-value" style={{ color: (kpis?.dso_days ?? 0) > 45 ? 'var(--color-neg)' : 'var(--color-pos)' }}>
            {kpis?.dso_days ?? '—'} <span style={{ fontSize: 14, fontWeight: 500 }}>days</span>
          </div>
          <div className="kpi-sub">Avg invoice {fmtMoneyCompact(kpis?.avg_invoice_size)}</div>
        </div>
      </div>

      {/* ── Cash Flow (hero chart) ────────────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <h2>Cash Flow: Invoiced vs Collected</h2>
          <div className="muted">
            {kpis && <>
              Invoiced {fmtMoneyCompact(kpis.total_invoiced)} ·
              Collected {fmtMoneyCompact(kpis.total_collected)} ·
              Credits {fmtMoneyCompact(kpis.total_credit_memos)} ·
              Write-Offs {fmtMoneyCompact(kpis.total_writeoffs)}
            </>}
          </div>
        </div>
        {cashflow && <CashFlowChart data={cashflow} />}
      </div>

      {/* ── AR Trend + Net AR Change ──────────────────────────────────────── */}
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
          {cashflow && <NetARChangeChart data={cashflow} />}
        </div>
      </div>

      {/* ── Aging donut + Exception pie ───────────────────────────────────── */}
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

      {/* ── Top Customers Bar ─────────────────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <h2>Top 10 Open Customer Balances</h2>
          <Link to="/invoices?status=Open" className="muted">View invoices →</Link>
        </div>
        <TopCustomersBar data={top_customers} />
      </div>

      {/* ── Exception Queue + Period Movement ─────────────────────────────── */}
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
              <tr style={{ fontWeight: 600, background: 'var(--color-surface)' }}>
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
