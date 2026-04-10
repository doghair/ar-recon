import urllib.request, json, sys

REF = "pikdtkqjhsektckwrkkb"
TOKEN = "sbp_488a6b2de39e11e6fa1fd59f1382d9727cbae73a"
URL = f"https://api.supabase.com/v1/projects/{REF}/database/query"

def run(sql, label=""):
    data = json.dumps({"query": sql}).encode()
    req = urllib.request.Request(URL, data=data, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "curl/7.88.1",
        "Accept": "*/*",
    })
    try:
        with urllib.request.urlopen(req) as r:
            print(f"  OK  {label}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ERR {label}: {e.code} — {body[:300]}")
        sys.exit(1)

drops = [
    # views — no CASCADE (not supported via API); drop in dependency order
    "DROP VIEW IF EXISTS v_all_exceptions",
    "DROP VIEW IF EXISTS v_exceptions_missing_gl",
    "DROP VIEW IF EXISTS v_exceptions_duplicate_gl",
    "DROP VIEW IF EXISTS v_exceptions_unapplied_cash",
    "DROP VIEW IF EXISTS v_exceptions_unapplied_credits",
    "DROP VIEW IF EXISTS v_exceptions_short_pays",
    "DROP VIEW IF EXISTS v_exceptions_timing_diffs",
    "DROP VIEW IF EXISTS v_exceptions_writeoff_mismatch",
    "DROP VIEW IF EXISTS v_reconciliation_current",
    "DROP VIEW IF EXISTS v_reconciliation_summary",
    "DROP VIEW IF EXISTS v_gl_ar_running",
    "DROP VIEW IF EXISTS v_gl_ar_balance_by_period",
    "DROP VIEW IF EXISTS v_subledger_balance_by_period",
    "DROP VIEW IF EXISTS v_subledger_open_by_customer",
    "DROP VIEW IF EXISTS v_ar_aging",
    # tables — CASCADE for FK deps
    "DROP TABLE IF EXISTS reconciliation_items CASCADE",
    "DROP TABLE IF EXISTS reconciliation_periods CASCADE",
    "DROP TABLE IF EXISTS bank_statements CASCADE",
    "DROP TABLE IF EXISTS gl_entries CASCADE",
    "DROP TABLE IF EXISTS credit_memos CASCADE",
    "DROP TABLE IF EXISTS cash_receipts CASCADE",
    "DROP TABLE IF EXISTS invoices CASCADE",
    "DROP TABLE IF EXISTS customers CASCADE",
]

tables = [
    ("customers", """CREATE TABLE customers (
        customer_id    TEXT PRIMARY KEY,
        customer_name  TEXT NOT NULL,
        customer_type  TEXT NOT NULL,
        city           TEXT,
        state_country  TEXT,
        payment_terms  TEXT NOT NULL,
        credit_limit   DOUBLE PRECISION NOT NULL DEFAULT 0,
        ap_email       TEXT,
        ap_contact     TEXT
    )"""),
    ("invoices", """CREATE TABLE invoices (
        invoice_id          TEXT PRIMARY KEY,
        customer_id         TEXT NOT NULL REFERENCES customers(customer_id),
        invoice_date        DATE NOT NULL,
        due_date            DATE NOT NULL,
        period              TEXT NOT NULL,
        product_id          TEXT,
        product_description TEXT,
        product_category    TEXT,
        quantity            INTEGER,
        unit_price          DOUBLE PRECISION,
        gross_amount        DOUBLE PRECISION NOT NULL,
        discount_amount     DOUBLE PRECISION DEFAULT 0,
        net_amount          DOUBLE PRECISION NOT NULL,
        tax_amount          DOUBLE PRECISION DEFAULT 0,
        total_amount        DOUBLE PRECISION NOT NULL,
        status              TEXT NOT NULL,
        gl_entry_id         TEXT,
        salesperson         TEXT,
        territory           TEXT,
        po_number           TEXT,
        notes               TEXT
    )"""),
    ("idx_inv_customer", "CREATE INDEX idx_inv_customer ON invoices(customer_id)"),
    ("idx_inv_period",   "CREATE INDEX idx_inv_period ON invoices(period)"),
    ("idx_inv_status",   "CREATE INDEX idx_inv_status ON invoices(status)"),
    ("idx_inv_date",     "CREATE INDEX idx_inv_date ON invoices(invoice_date)"),
    ("cash_receipts", """CREATE TABLE cash_receipts (
        receipt_id         TEXT PRIMARY KEY,
        customer_id        TEXT NOT NULL REFERENCES customers(customer_id),
        receipt_date       DATE NOT NULL,
        amount             DOUBLE PRECISION NOT NULL,
        payment_method     TEXT,
        reference          TEXT,
        check_number       TEXT,
        invoice_id_applied TEXT REFERENCES invoices(invoice_id),
        amount_applied     DOUBLE PRECISION DEFAULT 0,
        bank_deposit_id    TEXT,
        status             TEXT NOT NULL,
        notes              TEXT
    )"""),
    ("idx_rcp_customer", "CREATE INDEX idx_rcp_customer ON cash_receipts(customer_id)"),
    ("idx_rcp_invoice",  "CREATE INDEX idx_rcp_invoice ON cash_receipts(invoice_id_applied)"),
    ("idx_rcp_date",     "CREATE INDEX idx_rcp_date ON cash_receipts(receipt_date)"),
    ("idx_rcp_status",   "CREATE INDEX idx_rcp_status ON cash_receipts(status)"),
    ("credit_memos", """CREATE TABLE credit_memos (
        memo_id               TEXT PRIMARY KEY,
        customer_id           TEXT NOT NULL REFERENCES customers(customer_id),
        memo_date             DATE NOT NULL,
        period                TEXT NOT NULL,
        amount                DOUBLE PRECISION NOT NULL,
        reason                TEXT,
        original_invoice_id   TEXT REFERENCES invoices(invoice_id),
        applied_to_invoice_id TEXT REFERENCES invoices(invoice_id),
        gl_entry_id           TEXT,
        status                TEXT NOT NULL,
        notes                 TEXT
    )"""),
    ("idx_cm_customer", "CREATE INDEX idx_cm_customer ON credit_memos(customer_id)"),
    ("idx_cm_status",   "CREATE INDEX idx_cm_status ON credit_memos(status)"),
    ("gl_entries", """CREATE TABLE gl_entries (
        entry_id     TEXT PRIMARY KEY,
        entry_date   DATE NOT NULL,
        period       TEXT NOT NULL,
        account_code TEXT NOT NULL,
        account_name TEXT NOT NULL,
        entry_type   TEXT NOT NULL,
        debit        DOUBLE PRECISION DEFAULT 0,
        credit       DOUBLE PRECISION DEFAULT 0,
        description  TEXT,
        source_doc   TEXT,
        customer_id  TEXT REFERENCES customers(customer_id),
        posted_by    TEXT,
        notes        TEXT
    )"""),
    ("idx_gl_period",   "CREATE INDEX idx_gl_period ON gl_entries(period)"),
    ("idx_gl_account",  "CREATE INDEX idx_gl_account ON gl_entries(account_code)"),
    ("idx_gl_source",   "CREATE INDEX idx_gl_source ON gl_entries(source_doc)"),
    ("idx_gl_customer", "CREATE INDEX idx_gl_customer ON gl_entries(customer_id)"),
    ("idx_gl_type",     "CREATE INDEX idx_gl_type ON gl_entries(entry_type)"),
    ("idx_gl_date",     "CREATE INDEX idx_gl_date ON gl_entries(entry_date)"),
    ("bank_statements", """CREATE TABLE bank_statements (
        line_id             TEXT PRIMARY KEY,
        bank_date           DATE NOT NULL,
        value_date          DATE,
        description         TEXT,
        debit               DOUBLE PRECISION DEFAULT 0,
        credit              DOUBLE PRECISION DEFAULT 0,
        deposit_id          TEXT,
        transaction_type    TEXT,
        matched_receipt_ids TEXT,
        reconciled          TEXT NOT NULL DEFAULT 'No',
        notes               TEXT
    )"""),
    ("idx_bnk_date",       "CREATE INDEX idx_bnk_date ON bank_statements(bank_date)"),
    ("idx_bnk_reconciled", "CREATE INDEX idx_bnk_reconciled ON bank_statements(reconciled)"),
    ("reconciliation_periods", """CREATE TABLE reconciliation_periods (
        period            TEXT PRIMARY KEY,
        status            TEXT NOT NULL DEFAULT 'Open',
        gl_balance        DOUBLE PRECISION,
        subledger_balance DOUBLE PRECISION,
        variance          DOUBLE PRECISION,
        reconciled_by     TEXT,
        reconciled_at     TIMESTAMP,
        locked_at         TIMESTAMP,
        notes             TEXT
    )"""),
    ("reconciliation_items", """CREATE TABLE reconciliation_items (
        item_id          BIGSERIAL PRIMARY KEY,
        period           TEXT NOT NULL REFERENCES reconciliation_periods(period),
        category         TEXT NOT NULL,
        entity_type      TEXT NOT NULL,
        entity_id        TEXT NOT NULL,
        customer_id      TEXT,
        amount           DOUBLE PRECISION,
        description      TEXT,
        status           TEXT NOT NULL DEFAULT 'Open',
        assigned_to      TEXT,
        resolution_notes TEXT,
        created_at       TIMESTAMP DEFAULT NOW(),
        resolved_at      TIMESTAMP
    )"""),
    ("idx_recon_period",   "CREATE INDEX idx_recon_period ON reconciliation_items(period)"),
    ("idx_recon_category", "CREATE INDEX idx_recon_category ON reconciliation_items(category)"),
    ("idx_recon_status",   "CREATE INDEX idx_recon_status ON reconciliation_items(status)"),
]

views = [
    ("v_gl_ar_balance_by_period", """CREATE VIEW v_gl_ar_balance_by_period AS
SELECT period,
       ROUND(SUM(debit)::NUMERIC,2)               AS total_debits,
       ROUND(SUM(credit)::NUMERIC,2)              AS total_credits,
       ROUND((SUM(debit)-SUM(credit))::NUMERIC,2) AS net_movement
FROM gl_entries WHERE account_code='1200'
GROUP BY period ORDER BY period"""),

    ("v_gl_ar_running", """CREATE VIEW v_gl_ar_running AS
SELECT period,
       ROUND(SUM(net_movement) OVER (ORDER BY period ROWS UNBOUNDED PRECEDING)::NUMERIC,2) AS running_balance
FROM (
    SELECT period, SUM(debit)-SUM(credit) AS net_movement
    FROM gl_entries WHERE account_code='1200' GROUP BY period
) t ORDER BY period"""),

    ("v_subledger_open_by_customer", """CREATE VIEW v_subledger_open_by_customer AS
SELECT i.customer_id, c.customer_name, c.customer_type,
       COUNT(*) AS open_invoice_count,
       ROUND(SUM(i.total_amount)::NUMERIC,2) AS gross_open,
       ROUND(COALESCE(SUM(r.amount_applied),0)::NUMERIC,2) AS cash_applied,
       ROUND(COALESCE(SUM(cm.amount),0)::NUMERIC,2) AS credit_applied,
       ROUND((SUM(i.total_amount)-COALESCE(SUM(r.amount_applied),0)-COALESCE(SUM(cm.amount),0))::NUMERIC,2) AS net_open_balance
FROM invoices i
JOIN customers c ON c.customer_id=i.customer_id
LEFT JOIN cash_receipts r ON r.invoice_id_applied=i.invoice_id AND r.status='Applied'
LEFT JOIN credit_memos cm ON cm.applied_to_invoice_id=i.invoice_id AND cm.status='Applied'
WHERE i.status IN ('Open','Short Pay - Open')
GROUP BY i.customer_id,c.customer_name,c.customer_type
ORDER BY net_open_balance DESC"""),

    ("v_subledger_balance_by_period", """CREATE VIEW v_subledger_balance_by_period AS
SELECT period,
       ROUND(SUM(invoiced)::NUMERIC,2) AS total_invoiced,
       ROUND(SUM(credited)::NUMERIC,2) AS total_credit_memos,
       ROUND(SUM(paid)::NUMERIC,2) AS total_applied_cash,
       ROUND((SUM(invoiced)-SUM(credited)-SUM(paid))::NUMERIC,2) AS subledger_net
FROM (
    SELECT period, SUM(total_amount) AS invoiced, 0 AS credited, 0 AS paid FROM invoices GROUP BY period
    UNION ALL
    SELECT period, 0, SUM(amount), 0 FROM credit_memos WHERE status='Applied' GROUP BY period
    UNION ALL
    SELECT TO_CHAR(receipt_date,'YYYY-MM') AS period, 0, 0, SUM(amount_applied)
    FROM cash_receipts WHERE status='Applied' GROUP BY TO_CHAR(receipt_date,'YYYY-MM')
) t GROUP BY period ORDER BY period"""),

    ("v_reconciliation_summary", """CREATE VIEW v_reconciliation_summary AS
SELECT gl.period,
       gl.net_movement AS gl_net_movement,
       COALESCE(sub.subledger_net,0) AS subledger_net_movement,
       ROUND((gl.net_movement-COALESCE(sub.subledger_net,0))::NUMERIC,2) AS variance
FROM v_gl_ar_balance_by_period gl
LEFT JOIN v_subledger_balance_by_period sub ON sub.period=gl.period
ORDER BY gl.period"""),

    ("v_reconciliation_current", """CREATE VIEW v_reconciliation_current AS
SELECT
    (SELECT ROUND((SUM(debit)-SUM(credit))::NUMERIC,2) FROM gl_entries WHERE account_code='1200') AS gl_ar_total,
    (SELECT ROUND(SUM(net_open_balance)::NUMERIC,2) FROM v_subledger_open_by_customer) AS subledger_open_total,
    (SELECT ROUND((SUM(debit)-SUM(credit))::NUMERIC,2) FROM gl_entries WHERE account_code='1200')
    -(SELECT ROUND(SUM(net_open_balance)::NUMERIC,2) FROM v_subledger_open_by_customer) AS variance"""),

    ("v_ar_aging", """CREATE VIEW v_ar_aging AS
SELECT i.customer_id, c.customer_name, i.invoice_id,
       i.invoice_date, i.due_date, i.total_amount AS invoice_amount,
       ROUND((i.total_amount
           - COALESCE((SELECT SUM(amount_applied) FROM cash_receipts WHERE invoice_id_applied=i.invoice_id AND status='Applied'),0)
           - COALESCE((SELECT SUM(amount) FROM credit_memos WHERE applied_to_invoice_id=i.invoice_id AND status='Applied'),0)
       )::NUMERIC,2) AS open_balance,
       (CURRENT_DATE - i.due_date)::INTEGER AS days_past_due,
       CASE
           WHEN (CURRENT_DATE - i.due_date) <= 0   THEN 'Current'
           WHEN (CURRENT_DATE - i.due_date) <= 30  THEN '1-30'
           WHEN (CURRENT_DATE - i.due_date) <= 60  THEN '31-60'
           WHEN (CURRENT_DATE - i.due_date) <= 90  THEN '61-90'
           WHEN (CURRENT_DATE - i.due_date) <= 120 THEN '91-120'
           ELSE '120+'
       END AS aging_bucket
FROM invoices i
JOIN customers c ON c.customer_id=i.customer_id
WHERE i.status IN ('Open','Short Pay - Open')"""),

    ("v_exceptions_missing_gl", """CREATE VIEW v_exceptions_missing_gl AS
SELECT 'Missing GL' AS category, i.invoice_id, i.customer_id, c.customer_name,
       i.invoice_date, i.total_amount AS amount,
       'Invoice posted to subledger but no GL AR entry found' AS description
FROM invoices i JOIN customers c ON c.customer_id=i.customer_id
LEFT JOIN gl_entries g ON g.source_doc=i.invoice_id AND g.account_code='1200'
          AND g.entry_type LIKE 'Invoice%' AND g.debit>0
WHERE g.entry_id IS NULL"""),

    ("v_exceptions_duplicate_gl", """CREATE VIEW v_exceptions_duplicate_gl AS
SELECT 'Duplicate GL' AS category, g.source_doc AS invoice_id, g.customer_id,
       COUNT(*) AS gl_post_count,
       ROUND(SUM(g.debit)::NUMERIC,2) AS total_debit_posted,
       'Invoice posted to GL multiple times' AS description
FROM gl_entries g
WHERE g.account_code='1200' AND g.entry_type LIKE 'Invoice%' AND g.debit>0
GROUP BY g.source_doc,g.customer_id HAVING COUNT(*)>1"""),

    ("v_exceptions_unapplied_cash", """CREATE VIEW v_exceptions_unapplied_cash AS
SELECT 'Unapplied Cash' AS category, r.receipt_id, r.customer_id, c.customer_name,
       r.receipt_date, r.amount, r.payment_method, r.bank_deposit_id,
       'Cash received but not applied to any invoice' AS description
FROM cash_receipts r JOIN customers c ON c.customer_id=r.customer_id
WHERE r.status='Unapplied'"""),

    ("v_exceptions_unapplied_credits", """CREATE VIEW v_exceptions_unapplied_credits AS
SELECT 'Unapplied Credit' AS category, cm.memo_id, cm.customer_id, c.customer_name,
       cm.memo_date, cm.amount, cm.reason,
       'Credit memo issued but not applied to any invoice' AS description
FROM credit_memos cm JOIN customers c ON c.customer_id=cm.customer_id
WHERE cm.status='Unapplied'"""),

    ("v_exceptions_short_pays", """CREATE VIEW v_exceptions_short_pays AS
SELECT 'Short Pay' AS category, i.invoice_id, i.customer_id, c.customer_name,
       i.invoice_date, i.total_amount AS invoice_amount,
       COALESCE(SUM(r.amount_applied),0) AS paid_amount,
       ROUND((i.total_amount-COALESCE(SUM(r.amount_applied),0))::NUMERIC,2) AS short_paid_by,
       'Invoice underpaid; balance remains open' AS description
FROM invoices i JOIN customers c ON c.customer_id=i.customer_id
LEFT JOIN cash_receipts r ON r.invoice_id_applied=i.invoice_id AND r.status='Applied'
WHERE i.status='Short Pay - Open'
GROUP BY i.invoice_id,i.customer_id,c.customer_name,i.invoice_date,i.total_amount"""),

    ("v_exceptions_timing_diffs", """CREATE VIEW v_exceptions_timing_diffs AS
SELECT 'Timing Diff' AS category, b.line_id, b.bank_date, b.value_date,
       b.deposit_id, b.credit AS amount,
       (b.bank_date-b.value_date)::INTEGER AS lag_days,
       'Bank clear date differs from receipt date' AS description
FROM bank_statements b
WHERE b.bank_date<>b.value_date AND b.transaction_type='Deposit'"""),

    ("v_exceptions_writeoff_mismatch", """CREATE VIEW v_exceptions_writeoff_mismatch AS
SELECT 'Write-Off Mismatch' AS category, g.source_doc AS invoice_id, g.customer_id,
       g.entry_date, g.debit AS amount, i.status AS subledger_status,
       'GL write-off posted; subledger status should reflect' AS description
FROM gl_entries g LEFT JOIN invoices i ON i.invoice_id=g.source_doc
WHERE g.entry_type='Write-Off' AND g.account_code='5500'"""),

    ("v_all_exceptions", """CREATE VIEW v_all_exceptions AS
SELECT category, invoice_id AS entity_id, customer_id, amount, description FROM v_exceptions_missing_gl
UNION ALL SELECT category, invoice_id, customer_id, total_debit_posted, description FROM v_exceptions_duplicate_gl
UNION ALL SELECT category, receipt_id, customer_id, amount, description FROM v_exceptions_unapplied_cash
UNION ALL SELECT category, memo_id, customer_id, amount, description FROM v_exceptions_unapplied_credits
UNION ALL SELECT category, invoice_id, customer_id, short_paid_by, description FROM v_exceptions_short_pays
UNION ALL SELECT category, line_id, NULL, amount, description FROM v_exceptions_timing_diffs
UNION ALL SELECT category, invoice_id, customer_id, amount, description FROM v_exceptions_writeoff_mismatch"""),
]

print("Dropping existing objects...")
for sql in drops:
    name = sql.replace("DROP VIEW IF EXISTS ", "").replace("DROP TABLE IF EXISTS ", "").replace(" CASCADE", "")
    run(sql, name)

print("\nCreating tables & indexes...")
for label, sql in tables:
    run(sql, label)

print("\nCreating views...")
for label, sql in views:
    run(sql, label)

print("\nSchema complete!")
