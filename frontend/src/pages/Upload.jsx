import { useState, useRef } from 'react'

const BASE = import.meta.env.VITE_API_URL || ''

const TABLES = [
  { value: 'invoices',        label: 'Invoices',         pk: 'invoice_id' },
  { value: 'customers',       label: 'Customers',        pk: 'customer_id' },
  { value: 'cash_receipts',   label: 'Cash Receipts',    pk: 'receipt_id' },
  { value: 'credit_memos',    label: 'Credit Memos',     pk: 'memo_id' },
  { value: 'gl_entries',      label: 'GL Entries',       pk: 'entry_id' },
  { value: 'bank_statements', label: 'Bank Statements',  pk: 'line_id' },
]

export default function Upload() {
  const [table, setTable]   = useState('invoices')
  const [file, setFile]     = useState(null)
  const [dragging, setDrag] = useState(false)
  const [loading, setLoad]  = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError]   = useState(null)
  const inputRef            = useRef()

  const tableInfo = TABLES.find(t => t.value === table)

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
      const res = await fetch(`${BASE}/api/upload/${table}`, { method: 'POST', body: form })
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

      <div className="card" style={{ maxWidth: 640 }}>
        <h2>1. Select Table</h2>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
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
        <p className="muted" style={{ marginTop: 8, marginBottom: 0, fontSize: 12 }}>
          Unique key: <strong>{tableInfo.pk}</strong> — rows with an existing key are skipped as duplicates.
        </p>
      </div>

      <div className="card" style={{ maxWidth: 640 }}>
        <h2>2. Drop Your CSV File</h2>
        <div
          onDragOver={e => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current.click()}
          style={{
            border: `2px dashed ${dragging ? 'var(--color-accent)' : 'var(--color-border)'}`,
            borderRadius: 8,
            padding: '40px 24px',
            textAlign: 'center',
            cursor: 'pointer',
            background: dragging ? '#f0f9ff' : '#fafafa',
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
          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={!file || loading}
          >
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
        <div className="card" style={{ maxWidth: 640, borderLeft: '4px solid var(--color-neg)' }}>
          <h2 style={{ color: 'var(--color-neg)' }}>Upload Failed</h2>
          <p style={{ margin: 0, fontFamily: 'monospace', fontSize: 13 }}>{error}</p>
        </div>
      )}

      {result && (
        <div className="card" style={{ maxWidth: 640, borderLeft: `4px solid ${result.errors?.length ? 'var(--color-warn)' : 'var(--color-pos)'}` }}>
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
              <div style={{ maxHeight: 200, overflowY: 'auto', background: '#fafafa', borderRadius: 4, padding: '8px 12px', fontSize: 12, fontFamily: 'monospace' }}>
                {result.errors.map((e, i) => <div key={i}>{e}</div>)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
