export default function Compliance() {
  const reports = [
    {
      title: 'SOX Compliance — Section 404',
      desc: 'Internal controls over financial reporting. AR reconciliation evidence, segregation of duties, exception resolution audit trail.',
      status: 'Planned',
    },
    {
      title: 'Revenue Recognition — ASC 606',
      desc: 'Five-step model compliance tracking. Contract identification, performance obligation allocation, revenue timing validation.',
      status: 'Planned',
    },
    {
      title: '10-K / 10-Q Disclosures',
      desc: 'AR-related footnote preparation. Aging analysis, allowance for doubtful accounts, significant customer concentrations.',
      status: 'Planned',
    },
    {
      title: 'Credit Loss — CECL (ASC 326)',
      desc: 'Current expected credit loss estimation. Historical loss rates by aging bucket, forward-looking adjustments, reserve adequacy.',
      status: 'Planned',
    },
    {
      title: 'Audit Support Package',
      desc: 'PBC list automation. AR confirmations, rollforward schedules, cutoff testing support, subsequent collections analysis.',
      status: 'Planned',
    },
    {
      title: 'Intercompany Eliminations',
      desc: 'AR/AP intercompany matching and elimination entries for consolidated reporting.',
      status: 'Planned',
    },
  ]

  return (
    <div className="page">
      <div className="page-header">
        <h1>SEC Compliance Reporting</h1>
        <div className="muted">Regulatory reporting and audit support modules</div>
      </div>

      <div className="compliance-banner">
        <div className="compliance-banner-icon">&#9888;</div>
        <div>
          <strong>Under Development</strong> — These modules are being built to support
          SEC filing requirements, external audit workflows, and internal controls documentation.
          Data from the AR reconciliation engine will feed directly into each report.
        </div>
      </div>

      <div className="compliance-grid">
        {reports.map((r, i) => (
          <div key={i} className="card compliance-card">
            <div className="compliance-status">
              <span className="badge planned">{r.status}</span>
            </div>
            <h3>{r.title}</h3>
            <p className="muted">{r.desc}</p>
            <div className="compliance-actions">
              <button className="btn btn-outline" disabled>Configure</button>
              <button className="btn btn-outline" disabled>Generate</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
