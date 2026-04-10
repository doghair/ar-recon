-- ============================================================================
-- AR Reconciliation — Database Schema
-- Target: SQLite (portable to Postgres with minor type changes)
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ── Drop existing (dev-only reset) ──────────────────────────────────────────
DROP TABLE IF EXISTS reconciliation_items;
DROP TABLE IF EXISTS reconciliation_periods;
DROP TABLE IF EXISTS bank_statements;
DROP TABLE IF EXISTS gl_entries;
DROP TABLE IF EXISTS credit_memos;
DROP TABLE IF EXISTS cash_receipts;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS customers;

-- ── customers ───────────────────────────────────────────────────────────────
CREATE TABLE customers (
    customer_id      TEXT PRIMARY KEY,
    customer_name    TEXT NOT NULL,
    customer_type    TEXT NOT NULL,
    city             TEXT,
    state_country    TEXT,
    payment_terms    TEXT NOT NULL,
    credit_limit     REAL NOT NULL DEFAULT 0,
    ap_email         TEXT,
    ap_contact       TEXT
);

-- ── invoices (subledger) ────────────────────────────────────────────────────
CREATE TABLE invoices (
    invoice_id           TEXT PRIMARY KEY,
    customer_id          TEXT NOT NULL,
    invoice_date         DATE NOT NULL,
    due_date             DATE NOT NULL,
    period               TEXT NOT NULL,          -- 'YYYY-MM'
    product_id           TEXT,
    product_description  TEXT,
    product_category     TEXT,
    quantity             INTEGER,
    unit_price           REAL,
    gross_amount         REAL NOT NULL,
    discount_amount      REAL DEFAULT 0,
    net_amount           REAL NOT NULL,
    tax_amount           REAL DEFAULT 0,
    total_amount         REAL NOT NULL,
    status               TEXT NOT NULL,          -- Open | Paid | Short Pay - Open | Written Off
    gl_entry_id          TEXT,                   -- nullable for missing-GL scenario
    salesperson          TEXT,
    territory            TEXT,
    po_number            TEXT,
    notes                TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX idx_inv_customer ON invoices(customer_id);
CREATE INDEX idx_inv_period   ON invoices(period);
CREATE INDEX idx_inv_status   ON invoices(status);
CREATE INDEX idx_inv_date     ON invoices(invoice_date);

-- ── cash_receipts ───────────────────────────────────────────────────────────
CREATE TABLE cash_receipts (
    receipt_id            TEXT PRIMARY KEY,
    customer_id           TEXT NOT NULL,
    receipt_date          DATE NOT NULL,
    amount                REAL NOT NULL,
    payment_method        TEXT,                  -- ACH | Wire | Check | EFT
    reference             TEXT,
    check_number          TEXT,
    invoice_id_applied    TEXT,                  -- nullable when unapplied
    amount_applied        REAL DEFAULT 0,
    bank_deposit_id       TEXT,
    status                TEXT NOT NULL,         -- Applied | Unapplied | Partially Applied
    notes                 TEXT,
    FOREIGN KEY (customer_id)        REFERENCES customers(customer_id),
    FOREIGN KEY (invoice_id_applied) REFERENCES invoices(invoice_id)
);

CREATE INDEX idx_rcp_customer ON cash_receipts(customer_id);
CREATE INDEX idx_rcp_invoice  ON cash_receipts(invoice_id_applied);
CREATE INDEX idx_rcp_deposit  ON cash_receipts(bank_deposit_id);
CREATE INDEX idx_rcp_date     ON cash_receipts(receipt_date);
CREATE INDEX idx_rcp_status   ON cash_receipts(status);

-- ── credit_memos ────────────────────────────────────────────────────────────
CREATE TABLE credit_memos (
    memo_id                 TEXT PRIMARY KEY,
    customer_id             TEXT NOT NULL,
    memo_date               DATE NOT NULL,
    period                  TEXT NOT NULL,
    amount                  REAL NOT NULL,
    reason                  TEXT,
    original_invoice_id     TEXT,
    applied_to_invoice_id   TEXT,                -- nullable when unapplied
    gl_entry_id             TEXT,
    status                  TEXT NOT NULL,       -- Applied | Unapplied
    notes                   TEXT,
    FOREIGN KEY (customer_id)           REFERENCES customers(customer_id),
    FOREIGN KEY (original_invoice_id)   REFERENCES invoices(invoice_id),
    FOREIGN KEY (applied_to_invoice_id) REFERENCES invoices(invoice_id)
);

CREATE INDEX idx_cm_customer ON credit_memos(customer_id);
CREATE INDEX idx_cm_invoice  ON credit_memos(original_invoice_id);
CREATE INDEX idx_cm_status   ON credit_memos(status);

-- ── gl_entries (general ledger, double-entry) ───────────────────────────────
CREATE TABLE gl_entries (
    entry_id        TEXT PRIMARY KEY,
    entry_date      DATE NOT NULL,
    period          TEXT NOT NULL,
    account_code    TEXT NOT NULL,               -- 1000 Cash, 1200 AR, 2050 Suspense, 4000 Revenue, 5500 Bad Debt
    account_name    TEXT NOT NULL,
    entry_type      TEXT NOT NULL,               -- Invoice | Cash Receipt | Credit Memo | Write-Off | Unapplied Cash
    debit           REAL DEFAULT 0,
    credit          REAL DEFAULT 0,
    description     TEXT,
    source_doc      TEXT,                        -- invoice_id | receipt_id | memo_id
    customer_id     TEXT,
    posted_by       TEXT,
    notes           TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX idx_gl_period    ON gl_entries(period);
CREATE INDEX idx_gl_account   ON gl_entries(account_code);
CREATE INDEX idx_gl_source    ON gl_entries(source_doc);
CREATE INDEX idx_gl_customer  ON gl_entries(customer_id);
CREATE INDEX idx_gl_type      ON gl_entries(entry_type);
CREATE INDEX idx_gl_date      ON gl_entries(entry_date);

-- ── bank_statements ─────────────────────────────────────────────────────────
CREATE TABLE bank_statements (
    line_id             TEXT PRIMARY KEY,
    bank_date           DATE NOT NULL,           -- when bank cleared it
    value_date          DATE,                    -- effective date (may differ)
    description         TEXT,
    debit               REAL DEFAULT 0,
    credit              REAL DEFAULT 0,
    deposit_id          TEXT,
    transaction_type    TEXT,                    -- Deposit | Bank Fee | Wire Fee | Transfer
    matched_receipt_ids TEXT,                    -- pipe-separated receipt IDs
    reconciled          TEXT NOT NULL DEFAULT 'No',  -- Yes | No
    notes               TEXT
);

CREATE INDEX idx_bnk_date      ON bank_statements(bank_date);
CREATE INDEX idx_bnk_deposit   ON bank_statements(deposit_id);
CREATE INDEX idx_bnk_reconciled ON bank_statements(reconciled);

-- ── reconciliation_periods (period lock/status) ─────────────────────────────
CREATE TABLE reconciliation_periods (
    period              TEXT PRIMARY KEY,        -- 'YYYY-MM'
    status              TEXT NOT NULL DEFAULT 'Open',  -- Open | In Progress | Reconciled | Locked
    gl_balance          REAL,
    subledger_balance   REAL,
    variance            REAL,
    reconciled_by       TEXT,
    reconciled_at       TIMESTAMP,
    locked_at           TIMESTAMP,
    notes               TEXT
);

-- ── reconciliation_items (exception queue) ──────────────────────────────────
CREATE TABLE reconciliation_items (
    item_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    period              TEXT NOT NULL,
    category            TEXT NOT NULL,           -- Missing GL | Duplicate GL | Short Pay | Unapplied Cash | Unapplied Credit | Timing Diff | Write-Off Mismatch | Other
    entity_type         TEXT NOT NULL,           -- invoice | receipt | gl_entry | credit_memo | bank_line
    entity_id           TEXT NOT NULL,
    customer_id         TEXT,
    amount              REAL,
    description         TEXT,
    status              TEXT NOT NULL DEFAULT 'Open',  -- Open | In Review | Resolved | Written Off
    assigned_to         TEXT,
    resolution_notes    TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at         TIMESTAMP,
    FOREIGN KEY (period) REFERENCES reconciliation_periods(period)
);

CREATE INDEX idx_recon_period   ON reconciliation_items(period);
CREATE INDEX idx_recon_category ON reconciliation_items(category);
CREATE INDEX idx_recon_status   ON reconciliation_items(status);
