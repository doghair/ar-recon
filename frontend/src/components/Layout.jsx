import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import ThemeToggle from './ThemeToggle.jsx'

export default function Layout({ children }) {
  const [open, setOpen] = useState(false)
  const link = ({ isActive }) => (isActive ? 'active' : '')
  const close = () => setOpen(false)

  return (
    <div className="layout">
      <div className="mobile-header">
        <button className="hamburger" onClick={() => setOpen(o => !o)} aria-label="Toggle menu">☰</button>
        <span className="mobile-header-title">AR RECON</span>
      </div>

      <div className={`sidebar-overlay${open ? ' open' : ''}`} onClick={close} />

      <aside className={`sidebar${open ? ' open' : ''}`} style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1 }}>
          <div className="sidebar-brand">
            <h1>AR RECON</h1>
            <div className="sub">Biotech Co · Q1 2026</div>
          </div>
          <nav>
            <NavLink to="/"                className={link} end           onClick={close}>Dashboard</NavLink>
            <NavLink to="/exceptions"      className={link}               onClick={close}>Exceptions</NavLink>
            <NavLink to="/aging"           className={link}               onClick={close}>AR Aging</NavLink>
            <NavLink to="/invoices"        className={link}               onClick={close}>Invoices</NavLink>
            <NavLink to="/receipts"        className={link}               onClick={close}>Cash Receipts</NavLink>
            <NavLink to="/gl-entries"      className={link}               onClick={close}>GL Entries</NavLink>
            <NavLink to="/bank-statements" className={link}               onClick={close}>Bank Statements</NavLink>

            <div className="sidebar-divider" />
            <NavLink to="/customers"       className={link}               onClick={close}>Customers</NavLink>
            <NavLink to="/periods"         className={link}               onClick={close}>Period Lock</NavLink>

            <div className="sidebar-divider" />
            <NavLink to="/compliance"      className={link}               onClick={close}>SEC Compliance</NavLink>
            <NavLink to="/upload"          className={link}               onClick={close}>Upload Data</NavLink>
          </nav>
        </div>
        <div className="sidebar-bottom">
          <ThemeToggle />
        </div>
      </aside>

      <main className="main">{children}</main>
    </div>
  )
}
