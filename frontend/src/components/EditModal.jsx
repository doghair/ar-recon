import { useState } from 'react'

/**
 * Generic edit modal.
 * fields: [{ key, label, type: 'text'|'select'|'date'|'number'|'email', options: ['...'] }]
 */
export default function EditModal({ title, fields, values, onSave, onClose }) {
  const [form, setForm] = useState({ ...values })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  function set(key, val) {
    setForm(f => ({ ...f, [key]: val }))
  }

  async function handleSave() {
    setSaving(true)
    setError(null)
    try {
      await onSave(form)
      onClose()
    } catch (e) {
      setError(e.message)
      setSaving(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal">
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="modal-body">
          {fields.map(f => (
            <label key={f.key} className="modal-field">
              <span className="modal-field-label">{f.label}</span>
              {f.type === 'select' ? (
                <select value={form[f.key] ?? ''} onChange={e => set(f.key, e.target.value)}>
                  {f.options.map(o => (
                    <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>
                  ))}
                </select>
              ) : (
                <input
                  type={f.type || 'text'}
                  value={form[f.key] ?? ''}
                  onChange={e => set(f.key, e.target.value)}
                />
              )}
            </label>
          ))}
          {error && <div className="modal-error">{error}</div>}
        </div>
        <div className="modal-footer">
          <button className="btn" onClick={onClose} disabled={saving}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}
