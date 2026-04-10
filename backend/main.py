"""
AR Reconciliation API — FastAPI backend.

Run:
    python backend/main.py
or:
    uvicorn backend.main:app --reload --port 8000
"""
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DB_PATH = Path(__file__).resolve().parent.parent / "db" / "arrecon.db"

app = FastAPI(title="AR Reconciliation API", version="0.2.0")

# Permissive CORS for local dev — frontend may live on a dynamic port
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query_all(sql: str, params: tuple = ()) -> list[dict]:
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def query_one(sql: str, params: tuple = ()) -> Optional[dict]:
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()):
    conn = get_conn()
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


# ── health ──────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "db": str(DB_PATH), "db_exists": DB_PATH.exists()}


# ── dashboard ───────────────────────────────────────────────────────────────
@app.get("/api/dashboard")
def dashboard():
    current = query_one("SELECT * FROM v_reconciliation_current")
    exception_counts = query_all("""
        SELECT category,
               COUNT(*) AS count,
               ROUND(SUM(amount), 2) AS total
        FROM v_all_exceptions
        GROUP BY category
        ORDER BY category
    """)
    aging = query_all("""
        SELECT aging_bucket,
               COUNT(*) AS count,
               ROUND(SUM(open_balance), 2) AS total
        FROM v_ar_aging
        GROUP BY aging_bucket
        ORDER BY CASE aging_bucket
            WHEN 'Current' THEN 1
            WHEN '1-30'   THEN 2
            WHEN '31-60'  THEN 3
            WHEN '61-90'  THEN 4
            WHEN '91-120' THEN 5
            ELSE 6
        END
    """)
    period_summary = query_all("SELECT * FROM v_reconciliation_summary")
    top_customers = query_all(
        "SELECT * FROM v_subledger_open_by_customer LIMIT 10"
    )
    return {
        "current": current,
        "exception_counts": exception_counts,
        "aging": aging,
        "period_summary": period_summary,
        "top_customers": top_customers,
    }


# ── cash flow ───────────────────────────────────────────────────────────────
@app.get("/api/cashflow")
def cashflow():
    """Monthly cash flow: invoiced, collected, credit memos, write-offs, net AR change."""
    invoiced = query_all("""
        SELECT period,
               ROUND(SUM(total_amount), 2) AS amount
        FROM invoices
        GROUP BY period
        ORDER BY period
    """)
    collected = query_all("""
        SELECT strftime('%Y-%m', receipt_date) AS period,
               ROUND(SUM(amount), 2) AS amount
        FROM cash_receipts
        GROUP BY strftime('%Y-%m', receipt_date)
        ORDER BY period
    """)
    credit_memos = query_all("""
        SELECT strftime('%Y-%m', memo_date) AS period,
               ROUND(SUM(amount), 2) AS amount
        FROM credit_memos
        GROUP BY strftime('%Y-%m', memo_date)
        ORDER BY period
    """)
    writeoffs = query_all("""
        SELECT period,
               ROUND(SUM(debit), 2) AS amount
        FROM gl_entries
        WHERE account_code = '5500'
          AND entry_type = 'Write-Off'
        GROUP BY period
        ORDER BY period
    """)

    all_periods = sorted(set(
        [r["period"] for r in invoiced]
        + [r["period"] for r in collected]
        + [r["period"] for r in credit_memos]
        + [r["period"] for r in writeoffs]
    ))

    def lookup(rows, p):
        for r in rows:
            if r["period"] == p:
                return r["amount"] or 0
        return 0

    result = []
    for p in all_periods:
        inv = lookup(invoiced, p)
        col = lookup(collected, p)
        cm  = lookup(credit_memos, p)
        wo  = lookup(writeoffs, p)
        result.append({
            "period":       p,
            "invoiced":     inv,
            "collected":    col,
            "credit_memos": cm,
            "writeoffs":    wo,
            "net_ar_change": round(inv - col - cm - wo, 2),
        })
    return result


# ── AR balance trend (running) ──────────────────────────────────────────────
@app.get("/api/ar-trend")
def ar_trend():
    return query_all("""
        SELECT period, running_balance
        FROM v_gl_ar_running
        ORDER BY period
    """)


@app.get("/api/ar-trend/daily")
def ar_trend_daily():
    return query_all("""
        SELECT entry_date,
               ROUND(SUM(debit - credit) OVER (ORDER BY entry_date, entry_id
                        ROWS UNBOUNDED PRECEDING), 2) AS running_balance
        FROM gl_entries
        WHERE account_code = '1200'
        ORDER BY entry_date, entry_id
    """)


# ── KPIs ────────────────────────────────────────────────────────────────────
@app.get("/api/kpis")
def kpis():
    totals = query_one("""
        SELECT
            (SELECT ROUND(SUM(total_amount), 2) FROM invoices)               AS total_invoiced,
            (SELECT ROUND(SUM(amount), 2) FROM cash_receipts)                AS total_collected,
            (SELECT ROUND(SUM(amount), 2) FROM cash_receipts WHERE status = 'Applied') AS total_applied,
            (SELECT ROUND(SUM(amount), 2) FROM credit_memos)                 AS total_credit_memos,
            (SELECT ROUND(SUM(debit), 2)  FROM gl_entries
             WHERE account_code = '5500' AND entry_type = 'Write-Off')       AS total_writeoffs,
            (SELECT COUNT(*) FROM invoices)                                  AS invoice_count,
            (SELECT COUNT(*) FROM invoices WHERE status IN ('Open','Short Pay - Open')) AS open_invoice_count,
            (SELECT COUNT(*) FROM invoices WHERE status = 'Paid')            AS paid_invoice_count,
            (SELECT COUNT(*) FROM customers)                                 AS customer_count
    """)
    current = query_one("SELECT * FROM v_reconciliation_current")

    total_invoiced = totals.get("total_invoiced") or 0
    total_collected = totals.get("total_collected") or 0
    open_ar = current.get("subledger_open_total") if current else 0

    days_in_period = 99
    dso = round((open_ar / total_invoiced) * days_in_period, 1) if total_invoiced else 0
    collection_rate = round((total_collected / total_invoiced) * 100, 1) if total_invoiced else 0
    avg_invoice = round(total_invoiced / totals["invoice_count"], 2) if totals["invoice_count"] else 0

    return {
        **totals,
        "gl_ar_total":       current.get("gl_ar_total") if current else 0,
        "subledger_open":    open_ar,
        "variance":          current.get("variance") if current else 0,
        "dso_days":          dso,
        "collection_rate":   collection_rate,
        "avg_invoice_size":  avg_invoice,
    }


# ── reconciliation ──────────────────────────────────────────────────────────
@app.get("/api/reconciliation/current")
def recon_current():
    return query_one("SELECT * FROM v_reconciliation_current")


@app.get("/api/reconciliation/by-period")
def recon_by_period():
    return query_all("SELECT * FROM v_reconciliation_summary")


# ── exceptions ──────────────────────────────────────────────────────────────
EXCEPTION_VIEWS = {
    "Missing GL":          "v_exceptions_missing_gl",
    "Duplicate GL":        "v_exceptions_duplicate_gl",
    "Unapplied Cash":      "v_exceptions_unapplied_cash",
    "Unapplied Credit":    "v_exceptions_unapplied_credits",
    "Short Pay":           "v_exceptions_short_pays",
    "Timing Diff":         "v_exceptions_timing_diffs",
    "Write-Off Mismatch":  "v_exceptions_writeoff_mismatch",
}


@app.get("/api/exceptions")
def exceptions(category: Optional[str] = None):
    if category:
        return query_all(
            "SELECT * FROM v_all_exceptions WHERE category = ? ORDER BY amount DESC",
            (category,))
    return query_all("SELECT * FROM v_all_exceptions ORDER BY category, amount DESC")


@app.get("/api/exceptions/detail")
def exception_detail(category: str = Query(...)):
    view = EXCEPTION_VIEWS.get(category)
    if not view:
        raise HTTPException(404, f"Unknown category '{category}'")
    return query_all(f"SELECT * FROM {view}")


# ── reconciliation items (manual resolve) ───────────────────────────────────
class ResolveRequest(BaseModel):
    category: str
    entity_id: str
    customer_id: Optional[str] = None
    amount: Optional[float] = None
    resolution_notes: str = ""
    status: str = "Resolved"  # Resolved | Written Off | In Review


@app.get("/api/reconciliation/items")
def recon_items(category: Optional[str] = None, status: Optional[str] = None):
    clauses, params = [], []
    if category:
        clauses.append("category = ?"); params.append(category)
    if status:
        clauses.append("status = ?"); params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return query_all(
        f"SELECT * FROM reconciliation_items {where} ORDER BY created_at DESC",
        tuple(params))


@app.post("/api/reconciliation/items/resolve")
def resolve_exception(req: ResolveRequest):
    # Check if already resolved
    existing = query_one(
        "SELECT item_id FROM reconciliation_items WHERE category = ? AND entity_id = ? AND status IN ('Resolved','Written Off')",
        (req.category, req.entity_id))
    if existing:
        return {"ok": True, "message": "Already resolved", "item_id": existing["item_id"]}

    # Determine period from entity
    period = "2026-01"
    conn = get_conn()
    try:
        # Try to find the period from the entity
        row = conn.execute("SELECT period FROM invoices WHERE invoice_id = ?", (req.entity_id,)).fetchone()
        if row:
            period = row["period"]
        else:
            row = conn.execute("SELECT strftime('%Y-%m', receipt_date) as period FROM cash_receipts WHERE receipt_id = ?", (req.entity_id,)).fetchone()
            if row:
                period = row["period"]

        # Ensure the period row exists
        conn.execute("""
            INSERT OR IGNORE INTO reconciliation_periods (period, status)
            VALUES (?, 'Open')
        """, (period,))

        conn.execute("""
            INSERT INTO reconciliation_items
                (period, category, entity_type, entity_id, customer_id, amount, description, status, resolution_notes, resolved_at)
            VALUES (?, ?, 'auto', ?, ?, ?, ?, ?, ?, ?)
        """, (
            period,
            req.category,
            req.entity_id,
            req.customer_id,
            req.amount,
            f"Resolved: {req.category}",
            req.status,
            req.resolution_notes,
            datetime.utcnow().isoformat(),
        ))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "message": f"Exception marked as {req.status}"}


# ── period lock workflow ────────────────────────────────────────────────────
@app.get("/api/periods")
def list_periods():
    # Ensure periods exist for all months in the data
    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO reconciliation_periods (period, status)
            SELECT DISTINCT period, 'Open' FROM invoices
        """)
        conn.commit()
    finally:
        conn.close()

    # Enrich with computed balances
    periods = query_all("SELECT * FROM reconciliation_periods ORDER BY period")
    gl_balances = {r["period"]: r for r in query_all("SELECT * FROM v_gl_ar_balance_by_period")}
    sub_balances = {r["period"]: r for r in query_all("SELECT * FROM v_subledger_balance_by_period")}

    result = []
    for p in periods:
        gl = gl_balances.get(p["period"], {})
        sub = sub_balances.get(p["period"], {})
        gl_net = gl.get("net_movement", 0) or 0
        sub_net = sub.get("subledger_net", 0) or 0
        result.append({
            **p,
            "gl_balance": gl_net,
            "subledger_balance": sub_net,
            "variance": round(gl_net - sub_net, 2),
        })
    return result


@app.post("/api/periods/{period}/lock")
def lock_period(period: str):
    existing = query_one("SELECT * FROM reconciliation_periods WHERE period = ?", (period,))
    if not existing:
        execute(
            "INSERT INTO reconciliation_periods (period, status) VALUES (?, 'Open')",
            (period,))
    execute("""
        UPDATE reconciliation_periods
        SET status = 'Locked',
            reconciled_by = 'system',
            reconciled_at = ?,
            locked_at = ?
        WHERE period = ?
    """, (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), period))
    return {"ok": True, "message": f"Period {period} locked"}


@app.post("/api/periods/{period}/unlock")
def unlock_period(period: str):
    execute("""
        UPDATE reconciliation_periods
        SET status = 'Open',
            locked_at = NULL
        WHERE period = ?
    """, (period,))
    return {"ok": True, "message": f"Period {period} unlocked"}


# ── match engine ────────────────────────────────────────────────────────────
@app.get("/api/match/suggest/{receipt_id}")
def match_suggest(receipt_id: str):
    """Suggest open invoices that could match an unapplied cash receipt."""
    receipt = query_one(
        "SELECT * FROM cash_receipts WHERE receipt_id = ?",
        (receipt_id,))
    if not receipt:
        raise HTTPException(404, f"Receipt '{receipt_id}' not found")

    amt = receipt["amount"]
    cust = receipt["customer_id"]
    tolerance = 0.02  # 2% tolerance

    # Find open invoices for this customer within tolerance
    candidates = query_all("""
        SELECT
            i.invoice_id,
            i.customer_id,
            c.customer_name,
            i.invoice_date,
            i.due_date,
            i.total_amount,
            i.status,
            ABS(i.total_amount - ?) AS amount_diff,
            CASE
                WHEN ABS(i.total_amount - ?) < 0.01 THEN 100
                WHEN ABS(i.total_amount - ?) / i.total_amount <= 0.005 THEN 95
                WHEN ABS(i.total_amount - ?) / i.total_amount <= 0.02  THEN 80
                WHEN ABS(i.total_amount - ?) / i.total_amount <= 0.05  THEN 60
                ELSE 40
            END AS confidence
        FROM invoices i
        JOIN customers c ON c.customer_id = i.customer_id
        WHERE i.status IN ('Open', 'Short Pay - Open')
          AND i.customer_id = ?
          AND ABS(i.total_amount - ?) / i.total_amount <= ?
        ORDER BY confidence DESC, amount_diff ASC
        LIMIT 10
    """, (amt, amt, amt, amt, amt, cust, amt, tolerance))

    # Also check cross-customer matches (lower confidence)
    cross = query_all("""
        SELECT
            i.invoice_id,
            i.customer_id,
            c.customer_name,
            i.invoice_date,
            i.due_date,
            i.total_amount,
            i.status,
            ABS(i.total_amount - ?) AS amount_diff,
            CASE
                WHEN ABS(i.total_amount - ?) < 0.01 THEN 70
                WHEN ABS(i.total_amount - ?) / i.total_amount <= 0.005 THEN 60
                ELSE 30
            END AS confidence
        FROM invoices i
        JOIN customers c ON c.customer_id = i.customer_id
        WHERE i.status IN ('Open', 'Short Pay - Open')
          AND i.customer_id != ?
          AND ABS(i.total_amount - ?) < 0.01
        ORDER BY amount_diff ASC
        LIMIT 5
    """, (amt, amt, amt, cust, amt))

    return {
        "receipt": receipt,
        "same_customer": candidates,
        "cross_customer": cross,
    }


class MatchApplyRequest(BaseModel):
    receipt_id: str
    invoice_id: str


@app.post("/api/match/apply")
def match_apply(req: MatchApplyRequest):
    """Apply an unapplied receipt to an invoice."""
    receipt = query_one("SELECT * FROM cash_receipts WHERE receipt_id = ?", (req.receipt_id,))
    if not receipt:
        raise HTTPException(404, "Receipt not found")
    invoice = query_one("SELECT * FROM invoices WHERE invoice_id = ?", (req.invoice_id,))
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    conn = get_conn()
    try:
        # Update receipt
        conn.execute("""
            UPDATE cash_receipts
            SET status = 'Applied',
                invoice_id_applied = ?,
                amount_applied = amount
            WHERE receipt_id = ?
        """, (req.invoice_id, req.receipt_id))

        # Update invoice status if fully paid
        if abs(receipt["amount"] - invoice["total_amount"]) < 0.01:
            conn.execute("""
                UPDATE invoices SET status = 'Paid' WHERE invoice_id = ?
            """, (req.invoice_id,))
        else:
            conn.execute("""
                UPDATE invoices SET status = 'Short Pay - Open' WHERE invoice_id = ?
            """, (req.invoice_id,))

        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "message": f"Receipt {req.receipt_id} applied to {req.invoice_id}"}


# ── aging ───────────────────────────────────────────────────────────────────
@app.get("/api/aging")
def aging(
    customer_id: Optional[str] = None,
    bucket: Optional[str] = None,
):
    clauses, params = [], []
    if customer_id:
        clauses.append("customer_id = ?")
        params.append(customer_id)
    if bucket:
        clauses.append("aging_bucket = ?")
        params.append(bucket)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return query_all(
        f"SELECT * FROM v_ar_aging {where} ORDER BY days_past_due DESC",
        tuple(params))


@app.get("/api/aging/summary")
def aging_summary():
    return query_all("""
        SELECT aging_bucket,
               COUNT(*) AS count,
               ROUND(SUM(open_balance), 2) AS total
        FROM v_ar_aging
        GROUP BY aging_bucket
        ORDER BY CASE aging_bucket
            WHEN 'Current' THEN 1
            WHEN '1-30'   THEN 2
            WHEN '31-60'  THEN 3
            WHEN '61-90'  THEN 4
            WHEN '91-120' THEN 5
            ELSE 6
        END
    """)


# ── customers ───────────────────────────────────────────────────────────────
@app.get("/api/customers")
def customers():
    return query_all("SELECT * FROM customers ORDER BY customer_name")


@app.get("/api/customers/balances")
def customer_balances():
    return query_all("SELECT * FROM v_subledger_open_by_customer")


@app.get("/api/customers/{customer_id}")
def customer_detail(customer_id: str):
    row = query_one("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    if not row:
        raise HTTPException(404, f"Customer '{customer_id}' not found")
    return row


# ── invoices ────────────────────────────────────────────────────────────────
@app.get("/api/invoices")
def invoices(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    period: Optional[str] = None,
    limit: int = 500,
):
    clauses, params = [], []
    if status:
        clauses.append("status = ?"); params.append(status)
    if customer_id:
        clauses.append("customer_id = ?"); params.append(customer_id)
    if period:
        clauses.append("period = ?"); params.append(period)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return query_all(
        f"SELECT * FROM invoices {where} ORDER BY invoice_date DESC LIMIT ?",
        tuple(params))


# ── cash receipts ───────────────────────────────────────────────────────────
@app.get("/api/receipts")
def receipts(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    limit: int = 500,
):
    clauses, params = [], []
    if status:
        clauses.append("status = ?"); params.append(status)
    if customer_id:
        clauses.append("customer_id = ?"); params.append(customer_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return query_all(
        f"SELECT * FROM cash_receipts {where} ORDER BY receipt_date DESC LIMIT ?",
        tuple(params))


# ── GL entries ──────────────────────────────────────────────────────────────
@app.get("/api/gl-entries")
def gl_entries(
    account_code: Optional[str] = None,
    period: Optional[str] = None,
    entry_type: Optional[str] = None,
    limit: int = 500,
):
    clauses, params = [], []
    if account_code:
        clauses.append("account_code = ?"); params.append(account_code)
    if period:
        clauses.append("period = ?"); params.append(period)
    if entry_type:
        clauses.append("entry_type = ?"); params.append(entry_type)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return query_all(
        f"SELECT * FROM gl_entries {where} ORDER BY entry_date DESC, entry_id DESC LIMIT ?",
        tuple(params))


# ── bank statements ─────────────────────────────────────────────────────────
@app.get("/api/bank-statements")
def bank_statements(
    reconciled: Optional[str] = None,
    transaction_type: Optional[str] = None,
    limit: int = 500,
):
    clauses, params = [], []
    if reconciled:
        clauses.append("reconciled = ?"); params.append(reconciled)
    if transaction_type:
        clauses.append("transaction_type = ?"); params.append(transaction_type)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return query_all(
        f"SELECT * FROM bank_statements {where} ORDER BY bank_date DESC LIMIT ?",
        tuple(params))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    # reload disabled — uvicorn's reloader crashes on Windows due to CTRL_C_EVENT bug
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=False)
