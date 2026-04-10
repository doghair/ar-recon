import {
  BarChart, Bar,
  LineChart, Line,
  AreaChart, Area,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const COLORS = {
  invoiced:     '#1e3a5f',
  collected:    '#10b981',
  creditMemos:  '#f59e0b',
  writeoffs:    '#dc2626',
  netChange:    '#0ea5e9',
  arBalance:    '#6366f1',
  gridLine:     '#e2e8f0',
  axisLine:     '#94a3b8',
  tooltipBg:    '#0f172a',
}

const PIE_COLORS = [
  '#1e3a5f', '#0ea5e9', '#10b981', '#f59e0b',
  '#dc2626', '#8b5cf6', '#ec4899', '#14b8a6',
]

const AGING_COLORS = {
  'Current': '#10b981',
  '1-30':    '#3b82f6',
  '31-60':   '#f59e0b',
  '61-90':   '#f97316',
  '91-120':  '#dc2626',
  '120+':    '#991b1b',
}

const fmtK = (n) => {
  if (n === 0) return '$0'
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (Math.abs(n) >= 1_000)     return `$${(n / 1_000).toFixed(0)}K`
  return `$${n.toFixed(0)}`
}

const fmtMoney = (n) =>
  n == null ? '—' : '$' + Number(n).toLocaleString('en-US', {
    minimumFractionDigits: 0, maximumFractionDigits: 0,
  })

/* ── Custom tooltip ────────────────────────────────────────────────────── */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: COLORS.tooltipBg,
      color: 'white',
      padding: '10px 14px',
      borderRadius: 6,
      fontSize: 12,
      boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
    }}>
      <div style={{ fontWeight: 600, marginBottom: 6 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
          <span style={{ color: p.color }}>■ {p.name}:</span>
          <span style={{ fontVariantNumeric: 'tabular-nums' }}>{fmtMoney(p.value)}</span>
        </div>
      ))}
    </div>
  )
}

/* ── Cash Flow Bar Chart ───────────────────────────────────────────────── */
export function CashFlowChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.gridLine} />
        <XAxis dataKey="period" stroke={COLORS.axisLine} style={{ fontSize: 12 }} />
        <YAxis stroke={COLORS.axisLine} style={{ fontSize: 12 }} tickFormatter={fmtK} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(14, 165, 233, 0.05)' }} />
        <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
        <Bar dataKey="invoiced"     fill={COLORS.invoiced}    name="Invoiced"     radius={[4, 4, 0, 0]} />
        <Bar dataKey="collected"    fill={COLORS.collected}   name="Collected"    radius={[4, 4, 0, 0]} />
        <Bar dataKey="credit_memos" fill={COLORS.creditMemos} name="Credit Memos" radius={[4, 4, 0, 0]} />
        <Bar dataKey="writeoffs"    fill={COLORS.writeoffs}   name="Write-Offs"   radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

/* ── Net AR Change (bar with pos/neg colors) ──────────────────────────── */
export function NetARChangeChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.gridLine} />
        <XAxis dataKey="period" stroke={COLORS.axisLine} style={{ fontSize: 12 }} />
        <YAxis stroke={COLORS.axisLine} style={{ fontSize: 12 }} tickFormatter={fmtK} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(14, 165, 233, 0.05)' }} />
        <Bar dataKey="net_ar_change" name="Net AR Change" radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.net_ar_change >= 0 ? COLORS.invoiced : COLORS.collected} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

/* ── AR Balance Trend (area chart) ─────────────────────────────────────── */
export function ARTrendChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
        <defs>
          <linearGradient id="arGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor={COLORS.arBalance} stopOpacity={0.3} />
            <stop offset="95%" stopColor={COLORS.arBalance} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.gridLine} />
        <XAxis dataKey="period" stroke={COLORS.axisLine} style={{ fontSize: 12 }} />
        <YAxis stroke={COLORS.axisLine} style={{ fontSize: 12 }} tickFormatter={fmtK} />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="running_balance"
          name="AR Balance"
          stroke={COLORS.arBalance}
          strokeWidth={2.5}
          fillOpacity={1}
          fill="url(#arGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

/* ── AR Aging Donut ────────────────────────────────────────────────────── */
export function AgingDonut({ data }) {
  const chartData = data.map(d => ({
    name:  d.aging_bucket,
    value: d.total || 0,
    count: d.count,
  }))
  const total = chartData.reduce((s, d) => s + d.value, 0)

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          innerRadius={60}
          outerRadius={95}
          paddingAngle={2}
          dataKey="value"
        >
          {chartData.map((entry, i) => (
            <Cell key={i} fill={AGING_COLORS[entry.name] || PIE_COLORS[i % PIE_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const p = payload[0].payload
            const pct = total ? ((p.value / total) * 100).toFixed(1) : 0
            return (
              <div style={{
                background: COLORS.tooltipBg, color: 'white',
                padding: '10px 14px', borderRadius: 6, fontSize: 12,
              }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{p.name}</div>
                <div>{fmtMoney(p.value)}</div>
                <div style={{ opacity: 0.7 }}>{p.count} invoices · {pct}%</div>
              </div>
            )
          }}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          wrapperStyle={{ fontSize: 12 }}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}

/* ── Exception Pie ─────────────────────────────────────────────────────── */
export function ExceptionPie({ data }) {
  const chartData = data.map(d => ({
    name: d.category,
    value: d.total || 0,
    count: d.count,
  }))
  const total = chartData.reduce((s, d) => s + d.value, 0)

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          outerRadius={95}
          dataKey="value"
        >
          {chartData.map((entry, i) => (
            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const p = payload[0].payload
            const pct = total ? ((p.value / total) * 100).toFixed(1) : 0
            return (
              <div style={{
                background: COLORS.tooltipBg, color: 'white',
                padding: '10px 14px', borderRadius: 6, fontSize: 12,
              }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{p.name}</div>
                <div>{fmtMoney(p.value)}</div>
                <div style={{ opacity: 0.7 }}>{p.count} item(s) · {pct}%</div>
              </div>
            )
          }}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          wrapperStyle={{ fontSize: 11 }}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}

/* ── Top Customers Horizontal Bar ──────────────────────────────────────── */
export function TopCustomersBar({ data }) {
  const chartData = data.slice(0, 10).map(c => ({
    name:  c.customer_name.length > 28 ? c.customer_name.substring(0, 26) + '…' : c.customer_name,
    value: c.net_open_balance || 0,
    count: c.open_invoice_count,
  })).reverse()

  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.gridLine} horizontal={false} />
        <XAxis type="number" stroke={COLORS.axisLine} style={{ fontSize: 11 }} tickFormatter={fmtK} />
        <YAxis
          type="category"
          dataKey="name"
          stroke={COLORS.axisLine}
          style={{ fontSize: 11 }}
          width={180}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const p = payload[0].payload
            return (
              <div style={{
                background: COLORS.tooltipBg, color: 'white',
                padding: '10px 14px', borderRadius: 6, fontSize: 12,
              }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{p.name}</div>
                <div>{fmtMoney(p.value)}</div>
                <div style={{ opacity: 0.7 }}>{p.count} open invoices</div>
              </div>
            )
          }}
          cursor={{ fill: 'rgba(14, 165, 233, 0.05)' }}
        />
        <Bar dataKey="value" fill={COLORS.invoiced} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
