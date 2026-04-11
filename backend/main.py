"""
AR Reconciliation API — FastAPI backend (Supabase).
Uses supabase-py (PostgREST + RPC) — no direct DB password required.
"""
import io
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

# ── Supabase client ───────────────────────────────────────────────────────────
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

_client: Optional[Client] = None

def sb() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def tbl(name: str):
    return sb().table(name)


def rpc(fn: str, params: dict = {}):
    return sb().rpc(fn, params).execute().data


app = FastAPI(title="AR Reconciliation API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── health ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    result = tbl("customers").select("customer_id", count="exact").limit(0).execute()
    return {"status": "ok", "db": "supabase", "customer_count": result.count}


# ── dashboard ─────────────────────────────────────────────────────────────────
@app.get("/api/dashboard")
def dashboard():
    current          = tbl("v_reconciliation_current").select("*").execute().data
    exception_counts = tbl("v_all_exceptions").select("category,amount").execute().data
    aging            = tbl("v_ar_aging").select("aging_bucket,open_balance").execute().data
    period_summary   = tbl("v_reconciliation_summary").select("*").execute().data
    top_customers    = tbl("v_subledger_open_by_customer").select("*").limit(10).execute().data

    # Aggregate exception counts
    from collections import defaultdict
    exc_agg = defaultdict(lambda: {"count": 0, "total": 0.0})
    for r in exception_counts:
        exc_agg[r["category"]]["count"] += 1
        exc_agg[r["category"]]["total"] = round(exc_agg[r["category"]]["total"] + (r["amount"] or 0), 2)
    exc_list = sorted([{"category": k, "count": v["count"], "total": v["total"]}
                       for k, v in exc_agg.items()], key=lambda x: x["category"])

    # Aggregate aging
    bucket_order = {"Current": 1, "1-30": 2, "31-60": 3, "61-90": 4, "91-120": 5, "120+": 6}
    ag_agg = defaultdict(lambda: {"count": 0, "total": 0.0})
    for r in aging:
        b = r["aging_bucket"]
        ag_agg[b]["count"] += 1
        ag_agg[b]["total"] = round(ag_agg[b]["total"] + (r["open_balance"] or 0), 2)
    ag_list = sorted([{"aging_bucket": k, "count": v["count"], "total": v["total"]}
                      for k, v in ag_agg.items()], key=lambda x: bucket_order.get(x["aging_bucket"], 9))

    return {
        "current":          current[0] if current else None,
        "exception_counts": exc_list,
        "aging":            ag_list,
        "period_summary":   period_summary,
        "top_customers":    top_customers,
    }


# ── cash flow ─────────────────────────────────────────────────────────────────
@app.get("/api/cashflow")
def cashflow(date_from: Optional[str] = None, date_to: Optional[str] = None):
    if not date_from and not date_to:
        return rpc("get_cashflow")

    from collections import defaultdict
    inv_q = tbl("invoices").select("period,invoice_date,total_amount,status").limit(10000)
    rcp_q = tbl("cash_receipts").select("receipt_date,amount").limit(10000)
    cm_q  = tbl("credit_memos").select("memo_date,amount").limit(10000)

    if date_from:
        inv_q = inv_q.gte("invoice_date", date_from)
        rcp_q = rcp_q.gte("receipt_date", date_from)
        cm_q  = cm_q.gte("memo_date", date_from)
    if date_to:
        inv_q = inv_q.lte("invoice_date", date_to)
        rcp_q = rcp_q.lte("receipt_date", date_to)
        cm_q  = cm_q.lte("memo_date", date_to)

    by_period: dict = defaultdict(lambda: {"period": "", "invoiced": 0.0, "collected": 0.0, "credits": 0.0, "writeoffs": 0.0})

    for r in inv_q.execute().data:
        p = r.get("period") or (r.get("invoice_date") or "")[:7]
        by_period[p]["period"] = p
        if r.get("status") == "Written Off":
            by_period[p]["writeoffs"] = round(by_period[p]["writeoffs"] + (r["total_amount"] or 0), 2)
        else:
            by_period[p]["invoiced"] = round(by_period[p]["invoiced"] + (r["total_amount"] or 0), 2)

    for r in rcp_q.execute().data:
        p = (r.get("receipt_date") or "")[:7]
        if p:
            by_period[p]["period"] = p
            by_period[p]["collected"] = round(by_period[p]["collected"] + (r["amount"] or 0), 2)

    for r in cm_q.execute().data:
        p = (r.get("memo_date") or "")[:7]
        if p:
            by_period[p]["period"] = p
            by_period[p]["credits"] = round(by_period[p]["credits"] + (r["amount"] or 0), 2)

    return sorted(by_period.values(), key=lambda x: x["period"])


# ── Data range ───────────────────────────────────────────────────────────────
@app.get("/api/data-range")
def data_range():
    """Return the min and max invoice_date across all invoices."""
    rows = tbl("invoices").select("invoice_date").order("invoice_date", desc=False).limit(1).execute().data
    rows_max = tbl("invoices").select("invoice_date").order("invoice_date", desc=True).limit(1).execute().data
    min_date = rows[0]["invoice_date"] if rows else None
    max_date = rows_max[0]["invoice_date"] if rows_max else None
    return {"min_date": min_date, "max_date": max_date}


# ── AR balance trend ──────────────────────────────────────────────────────────
@app.get("/api/ar-trend")
def ar_trend():
    return tbl("v_gl_ar_running").select("period,running_balance").execute().data


@app.get("/api/ar-trend/daily")
def ar_trend_daily():
    return tbl("v_ar_trend_daily").select("entry_date,running_balance").execute().data


# ── KPIs ──────────────────────────────────────────────────────────────────────
@app.get("/api/kpis")
def kpis(date_from: Optional[str] = None, date_to: Optional[str] = None):
    if date_from or date_to:
        # Compute KPIs from filtered tables
        inv_q = tbl("invoices").select("total_amount,status").limit(10000)
        rcp_q = tbl("cash_receipts").select("amount").limit(10000)
        cm_q  = tbl("credit_memos").select("amount").limit(10000)

        if date_from:
            inv_q = inv_q.gte("invoice_date", date_from)
            rcp_q = rcp_q.gte("receipt_date", date_from)
            cm_q  = cm_q.gte("memo_date", date_from)
        if date_to:
            inv_q = inv_q.lte("invoice_date", date_to)
            rcp_q = rcp_q.lte("receipt_date", date_to)
            cm_q  = cm_q.lte("memo_date", date_to)

        invoices = inv_q.execute().data
        receipts = rcp_q.execute().data
        memos    = cm_q.execute().data

        total_invoiced     = sum((r["total_amount"] or 0) for r in invoices if r.get("status") != "Written Off")
        total_collected    = sum((r["amount"] or 0) for r in receipts)
        total_writeoffs    = sum((r["total_amount"] or 0) for r in invoices if r.get("status") == "Written Off")
        total_credit_memos = sum((r["amount"] or 0) for r in memos)
        inv_count          = len([r for r in invoices if r.get("status") != "Written Off"])
        totals = {
            "total_invoiced":     round(total_invoiced, 2),
            "total_collected":    round(total_collected, 2),
            "total_writeoffs":    round(total_writeoffs, 2),
            "total_credit_memos": round(total_credit_memos, 2),
            "invoice_count":      inv_count,
            "open_invoice_count": len([r for r in invoices if r.get("status") in ("Open", "Short Pay - Open")]),
        }
    else:
        totals = rpc("get_kpis")

    # Current AR snapshot (always live, not period-filtered)
    current = tbl("v_reconciliation_current").select("*").execute().data
    current = current[0] if current else {}

    total_invoiced  = totals.get("total_invoiced") or 0
    total_collected = totals.get("total_collected") or 0
    open_ar         = current.get("subledger_open_total") or 0

    days_in_period  = 99
    dso             = round((open_ar / total_invoiced) * days_in_period, 1) if total_invoiced else 0
    collection_rate = round((total_collected / total_invoiced) * 100, 1) if total_invoiced else 0
    inv_count       = totals.get("invoice_count") or 0
    avg_invoice     = round(total_invoiced / inv_count, 2) if inv_count else 0

    return {
        **totals,
        "gl_ar_total":      current.get("gl_ar_total") or 0,
        "subledger_open":   open_ar,
        "variance":         current.get("variance") or 0,
        "dso_days":         dso,
        "collection_rate":  collection_rate,
        "avg_invoice_size": avg_invoice,
    }


# ── reconciliation ────────────────────────────────────────────────────────────
@app.get("/api/reconciliation/current")
def recon_current():
    data = tbl("v_reconciliation_current").select("*").execute().data
    return data[0] if data else None


@app.get("/api/reconciliation/by-period")
def recon_by_period():
    return tbl("v_reconciliation_summary").select("*").execute().data


# ── exceptions ────────────────────────────────────────────────────────────────
VIEW_MAP = {
    "Missing GL":         "v_exceptions_missing_gl",
    "Duplicate GL":       "v_exceptions_duplicate_gl",
    "Unapplied Cash":     "v_exceptions_unapplied_cash",
    "Unapplied Credit":   "v_exceptions_unapplied_credits",
    "Short Pay":          "v_exceptions_short_pays",
    "Timing Diff":        "v_exceptions_timing_diffs",
    "Write-Off Mismatch": "v_exceptions_writeoff_mismatch",
}


@app.get("/api/exceptions")
def exceptions(category: Optional[str] = None):
    q = tbl("v_all_exceptions").select("*")
    if category:
        q = q.eq("category", category)
    return q.order("category").execute().data


@app.get("/api/exceptions/detail")
def exception_detail(category: str = Query(...)):
    view = VIEW_MAP.get(category)
    if not view:
        raise HTTPException(404, f"Unknown category '{category}'")
    return tbl(view).select("*").execute().data


# ── reconciliation items ──────────────────────────────────────────────────────
class ResolveRequest(BaseModel):
    category: str
    entity_id: str
    customer_id: Optional[str] = None
    amount: Optional[float] = None
    resolution_notes: str = ""
    status: str = "Resolved"


@app.get("/api/reconciliation/items")
def recon_items(category: Optional[str] = None, status: Optional[str] = None):
    q = tbl("reconciliation_items").select("*")
    if category: q = q.eq("category", category)
    if status:   q = q.eq("status", status)
    return q.order("created_at", desc=True).execute().data


@app.post("/api/reconciliation/items/resolve")
def resolve_exception(req: ResolveRequest):
    existing = tbl("reconciliation_items").select("item_id")\
        .eq("category", req.category).eq("entity_id", req.entity_id)\
        .in_("status", ["Resolved", "Written Off"]).execute().data
    if existing:
        return {"ok": True, "message": "Already resolved", "item_id": existing[0]["item_id"]}

    # Determine period
    inv = tbl("invoices").select("period").eq("invoice_id", req.entity_id).execute().data
    period = inv[0]["period"] if inv else "2026-01"

    # Ensure period row exists
    tbl("reconciliation_periods").upsert({"period": period, "status": "Open"},
                                          on_conflict="period").execute()
    tbl("reconciliation_items").insert({
        "period": period, "category": req.category,
        "entity_type": "auto", "entity_id": req.entity_id,
        "customer_id": req.customer_id, "amount": req.amount,
        "description": f"Resolved: {req.category}", "status": req.status,
        "resolution_notes": req.resolution_notes,
        "resolved_at": datetime.utcnow().isoformat(),
    }).execute()
    return {"ok": True, "message": f"Exception marked as {req.status}"}


# ── period lock ───────────────────────────────────────────────────────────────
@app.get("/api/periods")
def list_periods():
    inv_periods = tbl("invoices").select("period").execute().data
    for row in inv_periods:
        tbl("reconciliation_periods").upsert(
            {"period": row["period"], "status": "Open"},
            on_conflict="period").execute()

    periods     = tbl("reconciliation_periods").select("*").order("period").execute().data
    gl_balances  = {r["period"]: r for r in tbl("v_gl_ar_balance_by_period").select("*").execute().data}
    sub_balances = {r["period"]: r for r in tbl("v_subledger_balance_by_period").select("*").execute().data}
    result = []
    for p in periods:
        gl  = gl_balances.get(p["period"], {})
        sub = sub_balances.get(p["period"], {})
        result.append({
            **p,
            "gl_balance":        gl.get("net_movement") or 0,
            "subledger_balance": sub.get("subledger_net") or 0,
            "variance":          round((gl.get("net_movement") or 0) - (sub.get("subledger_net") or 0), 2),
        })
    return result


@app.post("/api/periods/{period}/lock")
def lock_period(period: str):
    tbl("reconciliation_periods").upsert({"period": period, "status": "Open"},
                                          on_conflict="period").execute()
    now = datetime.utcnow().isoformat()
    tbl("reconciliation_periods").update({
        "status": "Locked", "reconciled_by": "system",
        "reconciled_at": now, "locked_at": now,
    }).eq("period", period).execute()
    return {"ok": True, "message": f"Period {period} locked"}


@app.post("/api/periods/{period}/unlock")
def unlock_period(period: str):
    tbl("reconciliation_periods").update({"status": "Open", "locked_at": None})\
        .eq("period", period).execute()
    return {"ok": True, "message": f"Period {period} unlocked"}


# ── match engine ──────────────────────────────────────────────────────────────
@app.get("/api/match/suggest/{receipt_id}")
def match_suggest(receipt_id: str):
    result = rpc("get_match_suggestions", {"p_receipt_id": receipt_id})
    if not result:
        raise HTTPException(404, f"Receipt '{receipt_id}' not found")
    return result


class MatchApplyRequest(BaseModel):
    receipt_id: str
    invoice_id: str


@app.post("/api/match/apply")
def match_apply(req: MatchApplyRequest):
    receipt = tbl("cash_receipts").select("*").eq("receipt_id", req.receipt_id).execute().data
    if not receipt:
        raise HTTPException(404, "Receipt not found")
    invoice = tbl("invoices").select("*").eq("invoice_id", req.invoice_id).execute().data
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    receipt, invoice = receipt[0], invoice[0]

    tbl("cash_receipts").update({
        "status": "Applied", "invoice_id_applied": req.invoice_id, "amount_applied": receipt["amount"]
    }).eq("receipt_id", req.receipt_id).execute()

    new_status = "Paid" if abs(receipt["amount"] - invoice["total_amount"]) < 0.01 else "Short Pay - Open"
    tbl("invoices").update({"status": new_status}).eq("invoice_id", req.invoice_id).execute()
    return {"ok": True, "message": f"Receipt {req.receipt_id} applied to {req.invoice_id}"}


# ── aging ─────────────────────────────────────────────────────────────────────
@app.get("/api/aging")
def aging(customer_id: Optional[str] = None, bucket: Optional[str] = None):
    q = tbl("v_ar_aging").select("*")
    if customer_id: q = q.eq("customer_id", customer_id)
    if bucket:      q = q.eq("aging_bucket", bucket)
    return q.order("days_past_due", desc=True).execute().data


@app.get("/api/aging/summary")
def aging_summary():
    rows = tbl("v_ar_aging").select("aging_bucket,open_balance").execute().data
    from collections import defaultdict
    agg = defaultdict(lambda: {"count": 0, "total": 0.0})
    for r in rows:
        b = r["aging_bucket"]
        agg[b]["count"] += 1
        agg[b]["total"] = round(agg[b]["total"] + (r["open_balance"] or 0), 2)
    order = {"Current": 1, "1-30": 2, "31-60": 3, "61-90": 4, "91-120": 5, "120+": 6}
    return sorted([{"aging_bucket": k, "count": v["count"], "total": v["total"]}
                   for k, v in agg.items()], key=lambda x: order.get(x["aging_bucket"], 9))


# ── customers ─────────────────────────────────────────────────────────────────
@app.get("/api/customers")
def customers():
    return tbl("customers").select("*").order("customer_name").execute().data


@app.get("/api/customers/balances")
def customer_balances():
    return tbl("v_subledger_open_by_customer").select("*").execute().data


@app.get("/api/customers/{customer_id}")
def customer_detail(customer_id: str):
    data = tbl("customers").select("*").eq("customer_id", customer_id).execute().data
    if not data:
        raise HTTPException(404, f"Customer '{customer_id}' not found")
    return data[0]


@app.patch("/api/customers/{customer_id}")
def update_customer(customer_id: str, body: dict):
    allowed = {"customer_name","customer_type","city","state_country",
               "payment_terms","credit_limit","ap_email","ap_contact"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        raise HTTPException(400, "No valid fields to update")
    result = tbl("customers").update(updates).eq("customer_id", customer_id).execute().data
    return result[0] if result else None


# ── invoices ──────────────────────────────────────────────────────────────────
@app.get("/api/invoices")
def invoices(status: Optional[str]=None, customer_id: Optional[str]=None,
             period: Optional[str]=None, limit: int=500):
    q = tbl("invoices").select("*")
    if status:      q = q.eq("status", status)
    if customer_id: q = q.eq("customer_id", customer_id)
    if period:      q = q.eq("period", period)
    return q.order("invoice_date", desc=True).limit(limit).execute().data


@app.patch("/api/invoices/{invoice_id}")
def update_invoice(invoice_id: str, body: dict):
    allowed = {"status","notes","salesperson","territory","po_number",
               "total_amount","net_amount","gross_amount","discount_amount","tax_amount"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        raise HTTPException(400, "No valid fields to update")
    result = tbl("invoices").update(updates).eq("invoice_id", invoice_id).execute().data
    return result[0] if result else None


# ── cash receipts ─────────────────────────────────────────────────────────────
@app.get("/api/receipts")
def receipts(status: Optional[str]=None, customer_id: Optional[str]=None, limit: int=500):
    q = tbl("cash_receipts").select("*")
    if status:      q = q.eq("status", status)
    if customer_id: q = q.eq("customer_id", customer_id)
    return q.order("receipt_date", desc=True).limit(limit).execute().data


@app.patch("/api/receipts/{receipt_id}")
def update_receipt(receipt_id: str, body: dict):
    allowed = {"status","notes","amount_applied","invoice_id_applied","payment_method","reference"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        raise HTTPException(400, "No valid fields to update")
    result = tbl("cash_receipts").update(updates).eq("receipt_id", receipt_id).execute().data
    return result[0] if result else None


# ── GL entries ────────────────────────────────────────────────────────────────
@app.get("/api/gl-entries")
def gl_entries(account_code: Optional[str]=None, period: Optional[str]=None,
               entry_type: Optional[str]=None, limit: int=500):
    q = tbl("gl_entries").select("*")
    if account_code: q = q.eq("account_code", account_code)
    if period:       q = q.eq("period", period)
    if entry_type:   q = q.eq("entry_type", entry_type)
    return q.order("entry_date", desc=True).limit(limit).execute().data


# ── bank statements ───────────────────────────────────────────────────────────
@app.get("/api/bank-statements")
def bank_statements(reconciled: Optional[str]=None, transaction_type: Optional[str]=None, limit: int=500):
    q = tbl("bank_statements").select("*")
    if reconciled:       q = q.eq("reconciled", reconciled)
    if transaction_type: q = q.eq("transaction_type", transaction_type)
    return q.order("bank_date", desc=True).limit(limit).execute().data


# ── spreadsheet upload ────────────────────────────────────────────────────────
UPLOAD_TABLES = {
    "invoices":        ("invoice_id",  ["invoice_id","customer_id","invoice_date","due_date","period",
                                         "product_id","product_description","product_category","quantity",
                                         "unit_price","gross_amount","discount_amount","net_amount",
                                         "tax_amount","total_amount","status","salesperson","territory",
                                         "po_number","notes"]),
    "customers":       ("customer_id", ["customer_id","customer_name","customer_type","city",
                                         "state_country","payment_terms","credit_limit","ap_email","ap_contact"]),
    "cash_receipts":   ("receipt_id",  ["receipt_id","customer_id","receipt_date","amount","payment_method",
                                         "reference","check_number","invoice_id_applied","amount_applied",
                                         "bank_deposit_id","status","notes"]),
    "credit_memos":    ("memo_id",     ["memo_id","customer_id","memo_date","period","amount","reason",
                                         "original_invoice_id","applied_to_invoice_id","gl_entry_id",
                                         "status","notes"]),
    "gl_entries":      ("entry_id",    ["entry_id","entry_date","period","account_code","account_name",
                                         "entry_type","debit","credit","description","source_doc",
                                         "customer_id","posted_by","notes"]),
    "bank_statements": ("line_id",     ["line_id","bank_date","value_date","description","debit","credit",
                                         "deposit_id","transaction_type","matched_receipt_ids",
                                         "reconciled","notes"]),
}


@app.post("/api/upload/{table}")
async def upload_spreadsheet(table: str, file: UploadFile = File(...)):
    if table not in UPLOAD_TABLES:
        raise HTTPException(400, f"Unknown table '{table}'. Valid: {list(UPLOAD_TABLES)}")

    pk_col, valid_cols = UPLOAD_TABLES[table]

    try:
        import csv
        content = await file.read()
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    except Exception as e:
        raise HTTPException(400, f"Could not parse file: {e}")

    if not rows:
        return {"ok": True, "inserted": 0, "skipped_duplicates": 0, "errors": [], "total_rows": 0}

    if pk_col not in rows[0]:
        raise HTTPException(400, f"File must contain column '{pk_col}'")

    # Load existing PKs for duplicate detection
    existing_rows = tbl(table).select(pk_col).execute().data
    existing = {r[pk_col] for r in existing_rows}

    inserted, skipped, errors = 0, 0, []
    batch = []

    for i, row in enumerate(rows, 1):
        pk_val = (row.get(pk_col) or "").strip()
        if not pk_val:
            errors.append(f"Row {i}: missing {pk_col}")
            continue
        if pk_val in existing:
            skipped += 1
            continue

        record = {}
        for c in valid_cols:
            if c in row:
                v = (row[c] or "").strip()
                record[c] = None if v == "" else v
        batch.append(record)
        existing.add(pk_val)

        # Insert in batches of 100
        if len(batch) >= 100:
            try:
                tbl(table).insert(batch).execute()
                inserted += len(batch)
                batch = []
            except Exception as e:
                errors.append(f"Batch insert error: {str(e)[:100]}")
                batch = []

    if batch:
        try:
            tbl(table).insert(batch).execute()
            inserted += len(batch)
        except Exception as e:
            errors.append(f"Final batch error: {str(e)[:100]}")

    return {
        "ok": True,
        "inserted": inserted,
        "skipped_duplicates": skipped,
        "errors": errors,
        "total_rows": len(rows),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=False)
