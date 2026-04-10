"""Create PostgreSQL functions for complex queries in Supabase."""
import urllib.request, json, sys

REF   = "pikdtkqjhsektckwrkkb"
TOKEN = "sbp_488a6b2de39e11e6fa1fd59f1382d9727cbae73a"
URL   = f"https://api.supabase.com/v1/projects/{REF}/database/query"
HDR   = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
         "User-Agent": "curl/7.88.1", "Accept": "*/*"}

def run(sql, label=""):
    data = json.dumps({"query": sql}).encode()
    req = urllib.request.Request(URL, data=data, headers=HDR)
    try:
        with urllib.request.urlopen(req) as r:
            print(f"  OK  {label}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ERR {label}: {body[:300]}")
        sys.exit(1)

DQ = "$$"  # dollar-quoting delimiter — avoids shell expansion

# ── Drop existing ─────────────────────────────────────────────────────────────
run("DROP FUNCTION IF EXISTS get_cashflow() CASCADE", "drop get_cashflow")
run("DROP FUNCTION IF EXISTS get_kpis() CASCADE", "drop get_kpis")
run("DROP VIEW IF EXISTS v_ar_trend_daily", "drop v_ar_trend_daily")
run("DROP FUNCTION IF EXISTS get_match_suggestions(TEXT) CASCADE", "drop get_match_suggestions")

# ── cashflow monthly aggregation ──────────────────────────────────────────────
run(f"""
CREATE OR REPLACE FUNCTION get_cashflow()
RETURNS TABLE(
    period TEXT, invoiced NUMERIC, collected NUMERIC,
    credit_memos NUMERIC, writeoffs NUMERIC, net_ar_change NUMERIC
)
LANGUAGE sql STABLE AS {DQ}
  WITH
    inv AS (SELECT period, ROUND(SUM(total_amount)::NUMERIC,2) AS amt FROM invoices GROUP BY period),
    col AS (SELECT TO_CHAR(receipt_date,'YYYY-MM') AS period, ROUND(SUM(amount)::NUMERIC,2) AS amt FROM cash_receipts GROUP BY 1),
    cm  AS (SELECT TO_CHAR(memo_date,'YYYY-MM') AS period, ROUND(SUM(amount)::NUMERIC,2) AS amt FROM credit_memos GROUP BY 1),
    wo  AS (SELECT period, ROUND(SUM(debit)::NUMERIC,2) AS amt FROM gl_entries WHERE account_code='5500' AND entry_type='Write-Off' GROUP BY period),
    periods AS (SELECT DISTINCT period FROM (SELECT period FROM inv UNION SELECT period FROM col UNION SELECT period FROM cm UNION SELECT period FROM wo) p)
  SELECT
    p.period,
    COALESCE(inv.amt,0),
    COALESCE(col.amt,0),
    COALESCE(cm.amt,0),
    COALESCE(wo.amt,0),
    COALESCE(inv.amt,0) - COALESCE(col.amt,0) - COALESCE(cm.amt,0) - COALESCE(wo.amt,0)
  FROM periods p
  LEFT JOIN inv ON inv.period=p.period
  LEFT JOIN col ON col.period=p.period
  LEFT JOIN cm  ON cm.period=p.period
  LEFT JOIN wo  ON wo.period=p.period
  ORDER BY p.period
{DQ}
""", "create get_cashflow")

# ── kpis snapshot ─────────────────────────────────────────────────────────────
run(f"""
CREATE OR REPLACE FUNCTION get_kpis()
RETURNS JSON LANGUAGE sql STABLE AS {DQ}
  SELECT row_to_json(t) FROM (
    SELECT
      (SELECT ROUND(SUM(total_amount)::NUMERIC,2) FROM invoices)               AS total_invoiced,
      (SELECT ROUND(SUM(amount)::NUMERIC,2) FROM cash_receipts)                AS total_collected,
      (SELECT ROUND(SUM(amount)::NUMERIC,2) FROM cash_receipts WHERE status='Applied') AS total_applied,
      (SELECT ROUND(SUM(amount)::NUMERIC,2) FROM credit_memos)                 AS total_credit_memos,
      (SELECT ROUND(SUM(debit)::NUMERIC,2) FROM gl_entries WHERE account_code='5500' AND entry_type='Write-Off') AS total_writeoffs,
      (SELECT COUNT(*) FROM invoices)                                           AS invoice_count,
      (SELECT COUNT(*) FROM invoices WHERE status IN ('Open','Short Pay - Open')) AS open_invoice_count,
      (SELECT COUNT(*) FROM invoices WHERE status='Paid')                       AS paid_invoice_count,
      (SELECT COUNT(*) FROM customers)                                          AS customer_count
  ) t
{DQ}
""", "create get_kpis")

# ── daily AR running balance (view) ───────────────────────────────────────────
run(f"""
CREATE VIEW v_ar_trend_daily AS
SELECT entry_date,
       ROUND(SUM(debit-credit) OVER (ORDER BY entry_date, entry_id ROWS UNBOUNDED PRECEDING)::NUMERIC,2) AS running_balance
FROM gl_entries WHERE account_code='1200'
ORDER BY entry_date, entry_id
""", "create v_ar_trend_daily")

# ── match suggestions ─────────────────────────────────────────────────────────
run(f"""
CREATE OR REPLACE FUNCTION get_match_suggestions(p_receipt_id TEXT)
RETURNS JSON LANGUAGE plpgsql STABLE AS {DQ}
DECLARE
  v_receipt JSON;
  v_amt  DOUBLE PRECISION;
  v_cust TEXT;
  v_same JSON;
  v_cross JSON;
BEGIN
  SELECT row_to_json(r) INTO v_receipt FROM cash_receipts r WHERE receipt_id=p_receipt_id;
  IF v_receipt IS NULL THEN RETURN NULL; END IF;
  v_amt  := (v_receipt->>'amount')::DOUBLE PRECISION;
  v_cust := v_receipt->>'customer_id';

  SELECT json_agg(t) INTO v_same FROM (
    SELECT i.invoice_id, i.customer_id, c.customer_name, i.invoice_date, i.due_date,
           i.total_amount, i.status, ABS(i.total_amount-v_amt) AS amount_diff,
           CASE WHEN ABS(i.total_amount-v_amt)<0.01 THEN 100
                WHEN ABS(i.total_amount-v_amt)/NULLIF(i.total_amount,0)<=0.005 THEN 95
                WHEN ABS(i.total_amount-v_amt)/NULLIF(i.total_amount,0)<=0.02  THEN 80
                WHEN ABS(i.total_amount-v_amt)/NULLIF(i.total_amount,0)<=0.05  THEN 60
                ELSE 40 END AS confidence
    FROM invoices i JOIN customers c ON c.customer_id=i.customer_id
    WHERE i.status IN ('Open','Short Pay - Open') AND i.customer_id=v_cust
      AND ABS(i.total_amount-v_amt)/NULLIF(i.total_amount,0)<=0.02
    ORDER BY confidence DESC, amount_diff ASC LIMIT 10
  ) t;

  SELECT json_agg(t) INTO v_cross FROM (
    SELECT i.invoice_id, i.customer_id, c.customer_name, i.invoice_date, i.due_date,
           i.total_amount, i.status, ABS(i.total_amount-v_amt) AS amount_diff, 60 AS confidence
    FROM invoices i JOIN customers c ON c.customer_id=i.customer_id
    WHERE i.status IN ('Open','Short Pay - Open') AND i.customer_id!=v_cust
      AND ABS(i.total_amount-v_amt)<0.01
    ORDER BY amount_diff LIMIT 5
  ) t;

  RETURN json_build_object(
    'receipt', v_receipt,
    'same_customer',  COALESCE(v_same, '[]'::json),
    'cross_customer', COALESCE(v_cross,'[]'::json)
  );
END
{DQ}
""", "create get_match_suggestions")

print("\nAll functions created!")
