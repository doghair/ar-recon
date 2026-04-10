import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api.js'
import { fmtMoney, fmtNum, exportToCsv } from '../utils.js'
import EditModal from '../components/EditModal.jsx'

const CUSTOMER_EDIT_FIELDS = [
  { key: 'ap_contact', label: 'AP Contact', type: 'text' },
  { key: 'ap_email', label: 'AP Email', type: 'email' },
  { key: 'payment_terms', label: 'Payment Terms', type: 'text' },
  { key: 'credit_limit', label: 'Credit Limit', type: 'number' },
  { key: 'customer_type', label: 'Customer Type', type: 'select', options: ['Biotech', 'Pharma', 'Academic', 'Hospital', 'CRO'] },
]

export default function CustomerDetail() {
  const { id } = useParams()
  const [cust, setCust] = useState(null)
  const [invoices, setInvoices] = useState([])
  const [receipts, setReceipts] = useState([])
  const [aging, setAging] = useState([])
  const [err, setErr] = useState(null)
  const [editingCustomer, setEditingCustomer] = useState(false)

  useEffect(() => {
    Promise.all([
      api.customerDetail(id),
      api.invoices({ customer_id: id, limit: 500 }),
      api.receipts({ customer_id: id, limit: 500 }),
      api.aging({ customer_id: id }),
    ])
      .then(([c, inv, rcp, ag]) => {
        setCust(c)
        setInvoices(inv)
        setReceipts(rcp)
        setAging(ag)
      })
      .catch(e => setErr(e.message))
  }, [id])

  async function handleCustomerSave(updated) {
    const changed = {}
    CUSTOMER_EDIT_FIELDS.forEach(f => {
      if (String(updated[f.key]) !== String(cust[f.key])) changed[f.key] = updated[f.key]
    })
    if (Object.keys(changed).length === 0) return
    await api.updateCustomer(id, changed)
    setCust(c => ({ ...c, ...changed }))
  }

  if (err) return <div className="loading">Error: {err}</div>
  if (!cust) return <div className="loading">Loading customer…</div>

  const openInv = invoices.filter(i => i.status === 'Open' || i.status === 'Short Pay - Open')
  const totalOpen = openInv.reduce((s, i) => s + (i.total_amount || 0), 0)
  const totalPaid = invoices.filter(i => i.status === 'Paid').reduce((s, i) => s + (i.total_amount || 0), 0)
  const totalReceipts = receipts.reduce((s, r) => s + (r.amount || 0), 0)

  return (
    <div className="page">
      <div className="page-header">
        <h1>
          <Link to="/customers" style={{ color: 'var(--color-muted)', fontWeight: 400 }}>Customers</Link>
          {' / '}
          {cust.customer_name}
        </h1>
        <div className="muted">{cust.customer_id} · {cust.customer_type}</div>
      </div>

      {/* KPI strip */}
      <div className="kpi-strip" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="kpi-card">
          <div className="kpi-label">Total Invoiced</div>
          <div className="kpi-value">{fmtMoney(totalOpen + totalPaid)}</div>
          <div className="kpi-sub">{fmtNum(invoices.length)} invoices</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Open Balance</div>
          <div className="kpi-value" style={{ color: totalOpen > 0 ? '#dc2626' : '#059669' }}>
            {fmtMoney(totalOpen)}
          </div>
          <div className="kpi-sub">{fmtNum(openInv.length)} open invoices</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Cash Received</div>
          <div className="kpi-value">{fmtMoney(totalReceipts)}</div>
          <div className="kpi-sub">{fmtNum(receipts.length)} receipts</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Credit Limit</div>
          <div className="kpi-value">{fmtMoney(cust.credit_limit)}</div>
          <div className="kpi-sub">
            Terms: {cust.payment_terms}
          </div>
        </div>
      </div>

      {/* Customer info card */}
      <div className="card">
        <div className="card-header">
          <h2>Customer Information</h2>
          <button className="btn btn-sm" onClick={() => setEditingCustomer(true)}>Edit</button>
        </div>
        <div className="detail-grid">
          <div><span className="muted">Location:</span> {cust.city}, {cust.state_country}</div>
          <div><span className="muted">AP Contact:</span> {cust.ap_contact || '—'}</div>
          <div><span className="muted">AP Email:</span> {cust.ap_email || '—'}</div>
          <div><span className="muted">Payment Terms:</span> {cust.payment_terms}</div>
          <div><span className="muted">Credit Limit:</span> {fmtMoney(cust.credit_limit)}</div>
          <div><span className="muted">Type:</span> {cust.customer_type}</div>
        </div>
      </div>

      {/* Aging breakdown */}
      {aging.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2>AR Aging</h2>
            <button className="btn btn-sm" onClick={() => exportToCsv(aging, `aging_${id}`)}>
              &#8615; Export
            </button>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Invoice</th>
                <th>Date</th>
                <th>Due</th>
                <th>Bucket</th>
                <th className="right">Days Past Due</th>
                <th className="right">Open Balance</th>
              </tr>
            </thead>
            <tbody>
              {aging.map(a => (
                <tr key={a.invoice_id}>
                  <td>{a.invoice_id}</td>
                  <td>{a.invoice_date}</td>
                  <td>{a.due_date}</td>
                  <td><span className={`badge ${a.aging_bucket === 'Current' ? 'paid' : a.days_past_due > 60 ? 'writeoff' : 'shortpay'}`}>{a.aging_bucket}</span></td>
                  <td className="right">{a.days_past_due}</td>
                  <td className="right">{fmtMoney(a.open_balance)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Recent invoices */}
      <div className="card">
        <div className="card-header">
          <h2>Invoices ({invoices.length})</h2>
          <button className="btn btn-sm" onClick={() => exportToCsv(invoices, `invoices_${id}`)}>
            &#8615; Export
          </button>
        </div>
        <div className="table-wrap" style={{ maxHeight: 400 }}>
          <table className="table">
            <thead>
              <tr>
                <th>Invoice</th>
                <th>Date</th>
                <th>Due</th>
                <th>Product</th>
                <th className="right">Total</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map(r => (
                <tr key={r.invoice_id}>
                  <td>{r.invoice_id}</td>
                  <td>{r.invoice_date}</td>
                  <td>{r.due_date}</td>
                  <td>{r.product_description}</td>
                  <td className="right">{fmtMoney(r.total_amount)}</td>
                  <td>
                    <span className={`badge ${
                      r.status === 'Paid' ? 'paid'
                      : r.status === 'Open' ? 'open'
                      : r.status === 'Short Pay - Open' ? 'shortpay'
                      : 'writeoff'
                    }`}>{r.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cash receipts */}
      <div className="card">
        <div className="card-header">
          <h2>Cash Receipts ({receipts.length})</h2>
          <button className="btn btn-sm" onClick={() => exportToCsv(receipts, `receipts_${id}`)}>
            &#8615; Export
          </button>
        </div>
        <div className="table-wrap" style={{ maxHeight: 400 }}>
          <table className="table">
            <thead>
              <tr>
                <th>Receipt</th>
                <th>Date</th>
                <th>Method</th>
                <th>Applied To</th>
                <th className="right">Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {receipts.map(r => (
                <tr key={r.receipt_id}>
                  <td>{r.receipt_id}</td>
                  <td>{r.receipt_date}</td>
                  <td>{r.payment_method}</td>
                  <td>{r.invoice_id_applied || '—'}</td>
                  <td className="right">{fmtMoney(r.amount)}</td>
                  <td>
                    <span className={`badge ${r.status === 'Applied' ? 'applied' : 'unapplied'}`}>
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {editingCustomer && (
        <EditModal
          title={`Edit ${cust.customer_name}`}
          fields={CUSTOMER_EDIT_FIELDS}
          values={cust}
          onSave={handleCustomerSave}
          onClose={() => setEditingCustomer(false)}
        />
      )}
    </div>
  )
}
