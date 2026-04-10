-- ============================================================================
-- AR Reconciliation — Core Views
-- These views do the heavy lifting for the reconciliation dashboard.
-- ============================================================================

DROP VIEW IF EXISTS v_gl_ar_balance_by_period;
DROP VIEW IF EXISTS v_gl_ar_running;
DROP VIEW IF EXISTS v_subledger_open_by_customer;
DROP VIEW IF EXISTS v_subledger_balance_by_period;
DROP VIEW IF EXISTS v_reconciliation_summary;
DROP VIEW IF EXISTS v_reconciliation_current;
DROP VIEW IF EXISTS v_ar_aging;
DROP VIEW IF EXISTS v_exceptions_missing_gl;
DROP VIEW IF EXISTS v_exceptions_duplicate_gl;
DROP VIEW IF EXISTS v_exceptions_unapplied_cash;
DROP VIEW IF EXISTS v_exceptions_unapplied_credits;
DROP VIEW IF EXISTS v_exceptions_short_pays;
DROP VIEW IF EXISTS v_exceptions_timing_diffs;
DROP VIEW IF EXISTS v_exceptions_writeoff_mismatch;
DROP VIEW IF EXISTS v_all_exceptions;

-- ── GL AR Control Account balance by period ────────────────────────────────
CREATE VIEW v_gl_ar_balance_by_period AS
SELECT
    period,
    ROUND(SUM(debit), 2)                    AS total_debits,
    ROUND(SUM(credit), 2)                   AS total_credits,
    ROUND(SUM(debit) - SUM(credit), 2)      AS net_movement
FROM gl_entries
WHERE account_code = '1200'
GROUP BY period
ORDER BY period;

-- GL AR running balance (cumulative) — end-of-period snapshot
CREATE VIEW v_gl_ar_running AS
SELECT
    period,
    ROUND(
        SUM(net_movement) OVER (ORDER BY period ROWS UNBOUNDED PRECEDING)
    , 2) AS running_balance
FROM (
    SELECT
        period,
        SUM(debit) - SUM(credit) AS net_movement
    FROM gl_entries
    WHERE account_code = '1200'
    GROUP BY period
) t
ORDER BY period;

-- ── Subledger: open AR by customer ─────────────────────────────────────────
CREATE VIEW v_subledger_open_by_customer AS
SELECT
    i.customer_id,
    c.customer_name,
    c.customer_type,
    COUNT(*)                                                    AS open_invoice_count,
    ROUND(SUM(i.total_amount), 2)                               AS gross_open,
    ROUND(COALESCE(SUM(r.amount_applied), 0), 2)                AS cash_applied,
    ROUND(COALESCE(SUM(cm.amount), 0), 2)                       AS credit_applied,
    ROUND(
        SUM(i.total_amount)
        - COALESCE(SUM(r.amount_applied), 0)
        - COALESCE(SUM(cm.amount), 0), 2
    )                                                           AS net_open_balance
FROM invoices i
JOIN customers c ON c.customer_id = i.customer_id
LEFT JOIN cash_receipts r
       ON r.invoice_id_applied = i.invoice_id
      AND r.status = 'Applied'
LEFT JOIN credit_memos cm
       ON cm.applied_to_invoice_id = i.invoice_id
      AND cm.status = 'Applied'
WHERE i.status IN ('Open', 'Short Pay - Open')
GROUP BY i.customer_id, c.customer_name, c.customer_type
ORDER BY net_open_balance DESC;

-- ── Subledger balance by period ────────────────────────────────────────────
-- Period-level movement in the subledger (invoices − credit memos − payments applied)
CREATE VIEW v_subledger_balance_by_period AS
SELECT
    period,
    ROUND(SUM(invoiced), 2)   AS total_invoiced,
    ROUND(SUM(credited), 2)   AS total_credit_memos,
    ROUND(SUM(paid), 2)       AS total_applied_cash,
    ROUND(SUM(invoiced) - SUM(credited) - SUM(paid), 2) AS subledger_net
FROM (
    SELECT period, SUM(total_amount) AS invoiced, 0 AS credited, 0 AS paid
    FROM invoices
    GROUP BY period
    UNION ALL
    SELECT period, 0, SUM(amount), 0
    FROM credit_memos
    WHERE status = 'Applied'
    GROUP BY period
    UNION ALL
    SELECT strftime('%Y-%m', receipt_date) AS period, 0, 0, SUM(amount_applied)
    FROM cash_receipts
    WHERE status = 'Applied'
    GROUP BY strftime('%Y-%m', receipt_date)
)
GROUP BY period
ORDER BY period;

-- Reconciliation summary (period movement): GL net vs Subledger net per month
-- Useful for spotting which period introduced a variance
CREATE VIEW v_reconciliation_summary AS
SELECT
    gl.period,
    gl.net_movement                              AS gl_net_movement,
    COALESCE(sub.subledger_net, 0)               AS subledger_net_movement,
    ROUND(gl.net_movement - COALESCE(sub.subledger_net, 0), 2) AS variance
FROM v_gl_ar_balance_by_period gl
LEFT JOIN v_subledger_balance_by_period sub ON sub.period = gl.period
ORDER BY gl.period;

-- Current snapshot reconciliation: total GL AR vs total open subledger
-- The headline number for the dashboard
CREATE VIEW v_reconciliation_current AS
SELECT
    (SELECT ROUND(SUM(debit) - SUM(credit), 2)
     FROM gl_entries WHERE account_code = '1200')       AS gl_ar_total,
    (SELECT ROUND(SUM(net_open_balance), 2)
     FROM v_subledger_open_by_customer)                 AS subledger_open_total,
    (SELECT ROUND(SUM(debit) - SUM(credit), 2)
     FROM gl_entries WHERE account_code = '1200')
    - (SELECT ROUND(SUM(net_open_balance), 2)
       FROM v_subledger_open_by_customer)               AS variance;

-- ── AR Aging (current, 30, 60, 90, 120+) ───────────────────────────────────
CREATE VIEW v_ar_aging AS
SELECT
    i.customer_id,
    c.customer_name,
    i.invoice_id,
    i.invoice_date,
    i.due_date,
    i.total_amount                                      AS invoice_amount,
    ROUND(
        i.total_amount
        - COALESCE((SELECT SUM(amount_applied)
                    FROM cash_receipts
                    WHERE invoice_id_applied = i.invoice_id
                      AND status = 'Applied'), 0)
        - COALESCE((SELECT SUM(amount)
                    FROM credit_memos
                    WHERE applied_to_invoice_id = i.invoice_id
                      AND status = 'Applied'), 0)
    , 2)                                                AS open_balance,
    CAST(julianday('2026-04-09') - julianday(i.due_date) AS INTEGER) AS days_past_due,
    CASE
        WHEN julianday('2026-04-09') - julianday(i.due_date) <= 0   THEN 'Current'
        WHEN julianday('2026-04-09') - julianday(i.due_date) <= 30  THEN '1-30'
        WHEN julianday('2026-04-09') - julianday(i.due_date) <= 60  THEN '31-60'
        WHEN julianday('2026-04-09') - julianday(i.due_date) <= 90  THEN '61-90'
        WHEN julianday('2026-04-09') - julianday(i.due_date) <= 120 THEN '91-120'
        ELSE '120+'
    END                                                 AS aging_bucket
FROM invoices i
JOIN customers c ON c.customer_id = i.customer_id
WHERE i.status IN ('Open','Short Pay - Open');

-- ============================================================================
-- EXCEPTION QUEUES
-- Each view surfaces one type of reconciling item.
-- ============================================================================

-- Missing GL: invoice exists in subledger, no corresponding GL AR entry
CREATE VIEW v_exceptions_missing_gl AS
SELECT
    'Missing GL' AS category,
    i.invoice_id,
    i.customer_id,
    c.customer_name,
    i.invoice_date,
    i.total_amount AS amount,
    'Invoice posted to subledger but no GL AR entry found' AS description
FROM invoices i
JOIN customers c ON c.customer_id = i.customer_id
LEFT JOIN gl_entries g
       ON g.source_doc = i.invoice_id
      AND g.account_code = '1200'
      AND g.entry_type LIKE 'Invoice%'
      AND g.debit > 0
WHERE g.entry_id IS NULL;

-- Duplicate GL: more than one AR debit posted for the same invoice
CREATE VIEW v_exceptions_duplicate_gl AS
SELECT
    'Duplicate GL' AS category,
    g.source_doc  AS invoice_id,
    g.customer_id,
    COUNT(*)      AS gl_post_count,
    ROUND(SUM(g.debit), 2) AS total_debit_posted,
    'Invoice posted to GL multiple times' AS description
FROM gl_entries g
WHERE g.account_code = '1200'
  AND g.entry_type LIKE 'Invoice%'
  AND g.debit > 0
GROUP BY g.source_doc, g.customer_id
HAVING COUNT(*) > 1;

-- Unapplied cash receipts
CREATE VIEW v_exceptions_unapplied_cash AS
SELECT
    'Unapplied Cash' AS category,
    r.receipt_id,
    r.customer_id,
    c.customer_name,
    r.receipt_date,
    r.amount,
    r.payment_method,
    r.bank_deposit_id,
    'Cash received but not applied to any invoice' AS description
FROM cash_receipts r
JOIN customers c ON c.customer_id = r.customer_id
WHERE r.status = 'Unapplied';

-- Unapplied credit memos
CREATE VIEW v_exceptions_unapplied_credits AS
SELECT
    'Unapplied Credit' AS category,
    cm.memo_id,
    cm.customer_id,
    c.customer_name,
    cm.memo_date,
    cm.amount,
    cm.reason,
    'Credit memo issued but not applied to any invoice' AS description
FROM credit_memos cm
JOIN customers c ON c.customer_id = cm.customer_id
WHERE cm.status = 'Unapplied';

-- Short pays
CREATE VIEW v_exceptions_short_pays AS
SELECT
    'Short Pay' AS category,
    i.invoice_id,
    i.customer_id,
    c.customer_name,
    i.invoice_date,
    i.total_amount                     AS invoice_amount,
    COALESCE(SUM(r.amount_applied),0)  AS paid_amount,
    ROUND(i.total_amount - COALESCE(SUM(r.amount_applied),0), 2) AS short_paid_by,
    'Invoice underpaid; balance remains open' AS description
FROM invoices i
JOIN customers c ON c.customer_id = i.customer_id
LEFT JOIN cash_receipts r
       ON r.invoice_id_applied = i.invoice_id
      AND r.status = 'Applied'
WHERE i.status = 'Short Pay - Open'
GROUP BY i.invoice_id, i.customer_id, c.customer_name, i.invoice_date, i.total_amount;

-- Timing differences: receipt dated before bank clear date
CREATE VIEW v_exceptions_timing_diffs AS
SELECT
    'Timing Diff' AS category,
    b.line_id,
    b.bank_date,
    b.value_date,
    b.deposit_id,
    b.credit AS amount,
    CAST(julianday(b.bank_date) - julianday(b.value_date) AS INTEGER) AS lag_days,
    'Bank clear date differs from receipt date' AS description
FROM bank_statements b
WHERE b.bank_date <> b.value_date
  AND b.transaction_type = 'Deposit';

-- Write-off mismatch: GL shows write-off but subledger not updated
-- (for this prototype we detect by cross-check — invoice status vs GL entry type)
CREATE VIEW v_exceptions_writeoff_mismatch AS
SELECT
    'Write-Off Mismatch' AS category,
    g.source_doc AS invoice_id,
    g.customer_id,
    g.entry_date,
    g.debit AS amount,
    i.status AS subledger_status,
    'GL write-off posted; subledger status should reflect' AS description
FROM gl_entries g
LEFT JOIN invoices i ON i.invoice_id = g.source_doc
WHERE g.entry_type = 'Write-Off'
  AND g.account_code = '5500';  -- bad debt expense

-- ── Union view: all exceptions combined (lightweight columns) ───────────────
CREATE VIEW v_all_exceptions AS
SELECT category, invoice_id AS entity_id, customer_id, amount, description
FROM v_exceptions_missing_gl
UNION ALL
SELECT category, invoice_id, customer_id, total_debit_posted, description
FROM v_exceptions_duplicate_gl
UNION ALL
SELECT category, receipt_id, customer_id, amount, description
FROM v_exceptions_unapplied_cash
UNION ALL
SELECT category, memo_id, customer_id, amount, description
FROM v_exceptions_unapplied_credits
UNION ALL
SELECT category, invoice_id, customer_id, short_paid_by, description
FROM v_exceptions_short_pays
UNION ALL
SELECT category, line_id, NULL, amount, description
FROM v_exceptions_timing_diffs
UNION ALL
SELECT category, invoice_id, customer_id, amount, description
FROM v_exceptions_writeoff_mismatch;
