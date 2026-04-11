import { useState, useRef } from 'react'

const BASE = import.meta.env.VITE_API_URL || ''

const TABLES = [
  { value: 'invoices',        label: 'Invoices',        pk: 'invoice_id' },
  { value: 'customers',       label: 'Customers',       pk: 'customer_id' },
  { value: 'cash_receipts',   label: 'Cash Receipts',   pk: 'receipt_id' },
  { value: 'credit_memos',    label: 'Credit Memos',    pk: 'memo_id' },
  { value: 'gl_entries',      label: 'GL Entries',      pk: 'entry_id' },
  { value: 'bank_statements', label: 'Bank Statements', pk: 'line_id' },
]

// CSV templates: [header columns], [example row values]
const TEMPLATES = {
  invoices: {
    columns: [
      'invoice_id', 'customer_id', 'invoice_date', 'due_date', 'period',
      'product_id', 'product_description', 'product_category',
      'quantity', 'unit_price', 'gross_amount', 'discount_amount',
      'net_amount', 'tax_amount', 'total_amount',
      'status', 'gl_entry_id', 'salesperson', 'territory', 'po_number', 'notes',
    ],
    notes: [
      'invoice_id — unique ID (e.g. INV-2026-001)',
      'customer_id — must match an existing customer_id',
      'invoice_date / due_date — YYYY-MM-DD format',
      'period — YYYY-MM format (e.g. 2026-01)',
      'status — Open | Paid | Short Pay - Open | Written Off',
      'gross_amount = quantity × unit_price before discount; net_amount = gross − discount; total_amount = net + tax',
    ],
    example: {
      invoice_id: 'INV-2026-001', customer_id: 'CUST-001',
      invoice_date: '2026-01-15', due_date: '2026-02-14', period: '2026-01',
      product_id: 'PROD-001', product_description: 'Research Reagents Kit', product_category: 'Reagents',
      quantity: '10', unit_price: '14500.00',
      gross_amount: '145000.00', discount_amount: '0', net_amount: '145000.00',
      tax_amount: '0', total_amount: '145000.00',
      status: 'Open', gl_entry_id: 'GL-2026-001', salesperson: 'Jane Smith',
      territory: 'West', po_number: 'PO-2026-001', notes: '',
    },
  },
  customers: {
    columns: [
      'customer_id', 'customer_name', 'customer_type',
      'city', 'state_country', 'payment_terms', 'credit_limit',
      'ap_email', 'ap_contact',
    ],
    notes: [
      'customer_id — unique ID (e.g. CUST-001)',
      'customer_type — Biotech | Pharma | Academic | Hospital | CRO',
      'payment_terms — e.g. Net 30, Net 60, Due on Receipt',
      'credit_limit — numeric dollar amount (no $ sign)',
    ],
    example: {
      customer_id: 'CUST-001', customer_name: 'Acme Biotech Inc', customer_type: 'Biotech',
      city: 'San Francisco', state_country: 'CA', payment_terms: 'Net 30',
      credit_limit: '500000', ap_email: 'ap@acmebiotech.com', ap_contact: 'Alex Johnson',
    },
  },
  cash_receipts: {
    columns: [
      'receipt_id', 'customer_id', 'receipt_date', 'amount',
      'payment_method', 'reference', 'check_number',
      'invoice_id_applied', 'amount_applied', 'bank_deposit_id', 'status', 'notes',
    ],
    notes: [
      'receipt_id — unique ID (e.g. RCP-2026-001)',
      'customer_id — must match an existing customer_id',
      'receipt_date — YYYY-MM-DD format',
      'payment_method — ACH | Wire | Check | Credit Card | Other',
      'invoice_id_applied — leave blank if unapplied',
      'status — Applied | Unapplied',
    ],
    example: {
      receipt_id: 'RCP-2026-001', customer_id: 'CUST-001',
      receipt_date: '2026-01-20', amount: '145000.00',
      payment_method: 'ACH', reference: 'ACH-20260120-001', check_number: '',
      invoice_id_applied: 'INV-2026-001', amount_applied: '145000.00',
      bank_deposit_id: 'DEP-2026-001', status: 'Applied', notes: '',
    },
  },
  credit_memos: {
    columns: [
      'memo_id', 'customer_id', 'memo_date', 'period', 'amount',
      'reason', 'original_invoice_id', 'applied_to_invoice_id',
      'gl_entry_id', 'status', 'notes',
    ],
    notes: [
      'memo_id — unique ID (e.g. CM-2026-001)',
      'customer_id — must match an existing customer_id',
      'memo_date — YYYY-MM-DD format',
      'period — YYYY-MM format',
      'amount — positive number (the credit amount)',
      'status — Open | Applied | Voided',
    ],
    example: {
      memo_id: 'CM-2026-001', customer_id: 'CUST-001',
      memo_date: '2026-01-25', period: '2026-01', amount: '5000.00',
      reason: 'Pricing Adjustment', original_invoice_id: 'INV-2026-001',
      applied_to_invoice_id: 'INV-2026-001', gl_entry_id: 'GL-2026-002',
      status: 'Applied', notes: '',
    },
  },
  gl_entries: {
    columns: [
      'entry_id', 'entry_date', 'period', 'account_code', 'account_name',
      'entry_type', 'debit', 'credit', 'description',
      'source_doc', 'customer_id', 'posted_by', 'notes',
    ],
    notes: [
      'entry_id — unique ID (e.g. GL-2026-001)',
      'entry_date — YYYY-MM-DD format',
      'period — YYYY-MM format',
      'account_code — e.g. 1200 for AR Control',
      'entry_type — AR | Cash | Memo | Adjustment | Other',
      'debit / credit — one should be 0; the other is the amount',
      'customer_id — optional; leave blank for non-AR entries',
    ],
    example: {
      entry_id: 'GL-2026-001', entry_date: '2026-01-15', period: '2026-01',
      account_code: '1200', account_name: 'Accounts Receivable',
      entry_type: 'AR', debit: '145000.00', credit: '0',
      description: 'Invoice INV-2026-001 posted', source_doc: 'INV-2026-001',
      customer_id: 'CUST-001', posted_by: 'System', notes: '',
    },
  },
  bank_statements: {
    columns: [
      'line_id', 'bank_date', 'value_date', 'description',
      'debit', 'credit', 'deposit_id', 'transaction_type',
      'matched_receipt_ids', 'reconciled', 'notes',
    ],
    notes: [
      'line_id — unique ID per bank line (e.g. BNK-2026-001)',
      'bank_date / value_date — YYYY-MM-DD format',
      'debit — money leaving the account; credit — money coming in',
      'transaction_type — ACH | Wire | Check | Fee | Other',
      'matched_receipt_ids — comma-separated receipt IDs if matched',
      'reconciled — Yes | No',
    ],
    example: {
      line_id: 'BNK-2026-001', bank_date: '2026-01-20', value_date: '2026-01-20',
      description: 'ACH PAYMENT FROM ACME BIOTECH INC', debit: '0', credit: '145000.00',
      deposit_id: 'DEP-2026-001', transaction_type: 'ACH',
      matched_receipt_ids: 'RCP-2026-001', reconciled: 'No', notes: '',
    },
  },
}

function downloadTemplate(tableValue, tableLabel) {
  const tmpl = TEMPLATES[tableValue]
  if (!tmpl) return

  const esc = (v) => {
    if (v === null || v === undefined) return ''
    const s = String(v)
    return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }

  const headerRow  = tmpl.columns.map(esc).join(',')
  const exampleRow = tmpl.columns.map(c => esc(tmpl.example[c] ?? '')).join(',')

  // Build notes block as commented lines (prefixed with #)
  const noteLines  = tmpl.notes.map(n => `# ${n}`).join('\r\n')
  const csv = '\ufeff' + noteLines + '\r\n' + headerRow + '\r\n' + exampleRow + '\r\n'

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `template_${tableValue}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export default function Upload() {
  const [table, setTable]   = useState('invoices')
  const [file, setFile]     = useState(null)
  const [dragging, setDrag] = useState(false)
  const [loading, setLoad]  = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError]   = useState(null)
  const inputRef            = useRef()

  const tableInfo = TABLES.find(t => t.value === table)
  const tmpl      = TEMPLATES[table]

  function handleDrop(e) {
    e.preventDefault(); setDrag(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  async function handleUpload() {
    if (!file) return
    setLoad(true); setResult(null); setError(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const res  = await fetch(`${BASE}/api/upload/${table}`, { method: 'POST', body: form })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || JSON.stringify(data))
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoad(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Upload Spreadsheet</h1>
        <span className="muted">Import CSV data · duplicates skipped automatically</span>
      </div>

      {/* Step 1 — select table */}
      <div className="card" style={{ maxWidth: 680 }}>
        <h2>1. Select Table</h2>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
          {TABLES.map(t => (
            <button
              key={t.value}
              className={`btn ${table === t.value ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => { setTable(t.value); setResult(null) }}
            >
              {t.label}
            </button>
          ))}
        </div>
        <p className="muted" style={{ margin: '0 0 12px', fontSize: 12 }}>
          Unique key: <strong>{tableInfo.pk}</strong> — rows with an existing key are skipped as duplicates.
        </p>

        {/* Template download + column hint */}
        <div style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 6,
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: 16,
        }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, fontSize: 12, marginBottom: 6 }}>
              Required columns ({tmpl.columns.length})
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-muted)', lineHeight: 1.8, fontFamily: 'monospace' }}>
              {tmpl.columns.join(' · ')}
            </div>
          </div>
          <button
            className="btn btn-sm"
            style={{ flexShrink: 0, whiteSpace: 'nowrap' }}
            onClick={() => downloadTemplate(table, tableInfo.label)}
          >
            &#8615; Template
          </button>
        </div>

        {/* Field notes */}
        <ul style={{ margin: '12px 0 0', paddingLeft: 18, fontSize: 12, color: 'var(--color-muted)', lineHeight: 1.9 }}>
          {tmpl.notes.map((n, i) => <li key={i}>{n}</li>)}
        </ul>
      </div>

      {/* Step 2 — drop file */}
      <div className="card" style={{ maxWidth: 680 }}>
        <h2>2. Drop Your CSV File</h2>
        <div
          onDragOver={e => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current.click()}
          style={{
            border: `2px dashed ${dragging ? 'var(--color-accent)' : 'var(--color-border)'}`,
            borderRadius: 8,
            padding: '36px 24px',
            textAlign: 'center',
            cursor: 'pointer',
            background: dragging ? 'var(--color-accent-bg)' : 'var(--color-surface)',
            transition: 'all 0.15s',
          }}
        >
          <div style={{ fontSize: 32, marginBottom: 8 }}>📂</div>
          {file
            ? <><strong>{file.name}</strong><div className="muted">{(file.size / 1024).toFixed(1)} KB</div></>
            : <><div style={{ fontWeight: 500 }}>Drop CSV here or click to browse</div>
               <div className="muted" style={{ marginTop: 4 }}>Accepts .csv files</div></>
          }
          <input
            ref={inputRef} type="file" accept=".csv"
            style={{ display: 'none' }}
            onChange={e => { if (e.target.files[0]) setFile(e.target.files[0]) }}
          />
        </div>

        <div style={{ marginTop: 16, display: 'flex', gap: 12, alignItems: 'center' }}>
          <button className="btn btn-primary" onClick={handleUpload} disabled={!file || loading}>
            {loading ? 'Uploading…' : 'Upload & Import'}
          </button>
          {file && (
            <button className="btn btn-outline" onClick={() => { setFile(null); setResult(null); setError(null) }}>
              Clear
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="card" style={{ maxWidth: 680, borderLeft: '4px solid var(--color-neg)' }}>
          <h2 style={{ color: 'var(--color-neg)' }}>Upload Failed</h2>
          <p style={{ margin: 0, fontFamily: 'monospace', fontSize: 13 }}>{error}</p>
        </div>
      )}

      {result && (
        <div className="card" style={{ maxWidth: 680, borderLeft: `4px solid ${result.errors?.length ? 'var(--color-warn)' : 'var(--color-pos)'}` }}>
          <h2>Import Complete</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: result.errors?.length ? 16 : 0 }}>
            <div className="kpi-card" style={{ borderLeftColor: 'var(--color-pos)' }}>
              <div className="kpi-label">Inserted</div>
              <div className="kpi-value" style={{ fontSize: 24, color: 'var(--color-pos)' }}>{result.inserted}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Skipped (dupes)</div>
              <div className="kpi-value" style={{ fontSize: 24 }}>{result.skipped_duplicates}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Total Rows</div>
              <div className="kpi-value" style={{ fontSize: 24 }}>{result.total_rows}</div>
            </div>
          </div>

          {result.errors?.length > 0 && (
            <div>
              <div style={{ fontWeight: 600, color: 'var(--color-warn)', marginBottom: 8 }}>
                {result.errors.length} row(s) had errors:
              </div>
              <div style={{ maxHeight: 200, overflowY: 'auto', background: 'var(--color-surface)', borderRadius: 4, padding: '8px 12px', fontSize: 12, fontFamily: 'monospace' }}>
                {result.errors.map((e, i) => <div key={i}>{e}</div>)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
