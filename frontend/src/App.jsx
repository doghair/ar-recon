import { Routes, Route, Link } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Exceptions from './pages/Exceptions.jsx'
import Aging from './pages/Aging.jsx'
import Invoices from './pages/Invoices.jsx'
import Receipts from './pages/Receipts.jsx'
import GLEntries from './pages/GLEntries.jsx'
import BankStatements from './pages/BankStatements.jsx'
import Customers from './pages/Customers.jsx'
import CustomerDetail from './pages/CustomerDetail.jsx'
import Periods from './pages/Periods.jsx'
import Compliance from './pages/Compliance.jsx'
import Upload from './pages/Upload.jsx'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/"                element={<Dashboard />} />
        <Route path="/exceptions"      element={<Exceptions />} />
        <Route path="/aging"           element={<Aging />} />
        <Route path="/invoices"        element={<Invoices />} />
        <Route path="/receipts"        element={<Receipts />} />
        <Route path="/gl-entries"      element={<GLEntries />} />
        <Route path="/bank-statements" element={<BankStatements />} />
        <Route path="/customers"       element={<Customers />} />
        <Route path="/customers/:id"   element={<CustomerDetail />} />
        <Route path="/periods"         element={<Periods />} />
        <Route path="/compliance"      element={<Compliance />} />
        <Route path="/upload"          element={<Upload />} />
        <Route path="*" element={
          <div className="page">
            <div className="page-header"><h1>Page Not Found</h1></div>
            <p className="muted">The page you are looking for does not exist.</p>
            <Link to="/">Back to Dashboard</Link>
          </div>
        } />
      </Routes>
    </Layout>
  )
}
