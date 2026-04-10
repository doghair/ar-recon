import { NavLink } from 'react-router-dom'

export default function Layout({ children }) {
  const link = ({ isActive }) => (isActive ? 'active' : '')
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>AR RECON</h1>
          <div className="sub">Biotech Co · Q1 2026</div>
        </div>
        <nav>
          <NavLink to="/"                className={link} end>Dashboard</NavLink>
          <NavLink to="/exceptions"      className={link}>Exceptions</NavLink>
          <NavLink to="/aging"           className={link}>AR Aging</NavLink>
          <NavLink to="/invoices"        className={link}>Invoices</NavLink>
          <NavLink to="/receipts"        className={link}>Cash Receipts</NavLink>
          <NavLink to="/gl-entries"      className={link}>GL Entries</NavLink>
          <NavLink to="/bank-statements" className={link}>Bank Statements</NavLink>

          <div className="sidebar-divider" />
          <NavLink to="/customers"       className={link}>Customers</NavLink>
          <NavLink to="/periods"         className={link}>Period Lock</NavLink>

          <div className="sidebar-divider" />
          <NavLink to="/compliance"      className={link}>SEC Compliance</NavLink>
        </nav>
      </aside>
      <main className="main">{children}</main>
    </div>
  )
}
