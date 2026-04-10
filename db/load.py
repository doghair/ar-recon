"""
Load the CSV files from ../data into a SQLite database.
Creates schema, imports data, creates views, runs validation queries.

Usage:  python db/load.py        (run from project root)
"""
import csv
import os
import sqlite3
import sys
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH  = ROOT / "db" / "arrecon.db"
SCHEMA   = ROOT / "db" / "schema.sql"
VIEWS    = ROOT / "db" / "views.sql"


def read_csv(filename):
    with open(DATA_DIR / filename, newline="") as f:
        return list(csv.DictReader(f))


def to_float(v):
    if v is None or v == "":
        return 0.0
    return float(v)


def to_int_or_null(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def nullable(v):
    return None if v == "" else v


def main():
    if DB_PATH.exists():
        print(f"Removing existing DB: {DB_PATH}")
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # 1. schema
    print(f"Applying schema: {SCHEMA}")
    cur.executescript(SCHEMA.read_text())

    # 2. customers
    rows = read_csv("customers.csv")
    cur.executemany(
        """INSERT INTO customers (customer_id, customer_name, customer_type,
               city, state_country, payment_terms, credit_limit, ap_email, ap_contact)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [(r["customer_id"], r["customer_name"], r["customer_type"],
          r["city"], r["state_country"], r["payment_terms"],
          to_float(r["credit_limit"]), r["ap_email"], r["ap_contact"])
         for r in rows])
    print(f"  customers      : {len(rows):>5} rows")

    # 3. invoices
    rows = read_csv("invoices.csv")
    cur.executemany(
        """INSERT INTO invoices (invoice_id, customer_id, invoice_date, due_date,
               period, product_id, product_description, product_category, quantity,
               unit_price, gross_amount, discount_amount, net_amount, tax_amount,
               total_amount, status, gl_entry_id, salesperson, territory,
               po_number, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [(r["invoice_id"], r["customer_id"], r["invoice_date"], r["due_date"],
          r["period"], r["product_id"], r["product_description"], r["product_category"],
          to_int_or_null(r["quantity"]), to_float(r["unit_price"]),
          to_float(r["gross_amount"]), to_float(r["discount_amount"]),
          to_float(r["net_amount"]), to_float(r["tax_amount"]),
          to_float(r["total_amount"]), r["status"], nullable(r["gl_entry_id"]),
          r["salesperson"], r["territory"], r["po_number"], r["notes"])
         for r in rows])
    print(f"  invoices       : {len(rows):>5} rows")

    # 4. cash_receipts
    rows = read_csv("cash_receipts.csv")
    cur.executemany(
        """INSERT INTO cash_receipts (receipt_id, customer_id, receipt_date, amount,
               payment_method, reference, check_number, invoice_id_applied,
               amount_applied, bank_deposit_id, status, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        [(r["receipt_id"], r["customer_id"], r["receipt_date"], to_float(r["amount"]),
          r["payment_method"], r["reference"], r["check_number"],
          nullable(r["invoice_id_applied"]), to_float(r["amount_applied"]),
          r["bank_deposit_id"], r["status"], r["notes"])
         for r in rows])
    print(f"  cash_receipts  : {len(rows):>5} rows")

    # 5. credit_memos
    rows = read_csv("credit_memos.csv")
    cur.executemany(
        """INSERT INTO credit_memos (memo_id, customer_id, memo_date, period,
               amount, reason, original_invoice_id, applied_to_invoice_id,
               gl_entry_id, status, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        [(r["memo_id"], r["customer_id"], r["memo_date"], r["period"],
          to_float(r["amount"]), r["reason"], nullable(r["original_invoice_id"]),
          nullable(r["applied_to_invoice_id"]), r["gl_entry_id"],
          r["status"], r["notes"])
         for r in rows])
    print(f"  credit_memos   : {len(rows):>5} rows")

    # 6. gl_entries
    rows = read_csv("gl_entries.csv")
    cur.executemany(
        """INSERT INTO gl_entries (entry_id, entry_date, period, account_code,
               account_name, entry_type, debit, credit, description, source_doc,
               customer_id, posted_by, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [(r["entry_id"], r["entry_date"], r["period"], r["account_code"],
          r["account_name"], r["entry_type"], to_float(r["debit"]),
          to_float(r["credit"]), r["description"], r["source_doc"],
          nullable(r["customer_id"]), r["posted_by"], r["notes"])
         for r in rows])
    print(f"  gl_entries     : {len(rows):>5} rows")

    # 7. bank_statements
    rows = read_csv("bank_statements.csv")
    cur.executemany(
        """INSERT INTO bank_statements (line_id, bank_date, value_date, description,
               debit, credit, deposit_id, transaction_type, matched_receipt_ids,
               reconciled, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        [(r["line_id"], r["bank_date"], r["value_date"], r["description"],
          to_float(r["debit"]), to_float(r["credit"]), r["deposit_id"],
          r["transaction_type"], r["matched_receipt_ids"],
          r["reconciled"], r["notes"])
         for r in rows])
    print(f"  bank_statements: {len(rows):>5} rows")

    # 8. views
    print(f"\nCreating views: {VIEWS}")
    cur.executescript(VIEWS.read_text())

    # 9. seed reconciliation_periods
    cur.executemany(
        """INSERT INTO reconciliation_periods (period, status) VALUES (?, 'Open')""",
        [("2026-01",), ("2026-02",), ("2026-03",)])

    conn.commit()

    # Validation queries
    print("\n" + "=" * 62)
    print("VALIDATION - Recon views")
    print("=" * 62)

    def section(title):
        print(f"\n-- {title} " + "-" * max(0, 58 - len(title)))

    def run(sql, headers=None):
        cur.execute(sql)
        results = cur.fetchall()
        if headers:
            print("  " + " | ".join(f"{h:>14}" for h in headers))
        for row in results:
            print("  " + " | ".join(
                f"{v:>14,.2f}" if isinstance(v, float)
                else f"{str(v):>14}" if v is not None
                else f"{'—':>14}"
                for v in row))
        return results

    section("GL AR balance by period")
    run("SELECT period, total_debits, total_credits, net_movement FROM v_gl_ar_balance_by_period",
        ["period", "debits", "credits", "net"])

    section("Reconciliation summary (per-period movement)")
    run("SELECT period, gl_net_movement, subledger_net_movement, variance FROM v_reconciliation_summary",
        ["period", "GL net", "subledger net", "variance"])

    section("Current snapshot: GL AR vs Subledger Open")
    run("SELECT gl_ar_total, subledger_open_total, variance FROM v_reconciliation_current",
        ["GL AR total", "Sub open", "variance"])

    section("Exception counts by category")
    cur.execute("""SELECT category, COUNT(*), ROUND(SUM(amount),2)
                   FROM v_all_exceptions GROUP BY category ORDER BY category""")
    for cat, cnt, amt in cur.fetchall():
        print(f"  {cat:<22} {cnt:>4}  ${amt:>14,.2f}")

    section("Top 5 open customer balances")
    cur.execute("""SELECT customer_name, open_invoice_count, net_open_balance
                   FROM v_subledger_open_by_customer LIMIT 5""")
    for name, cnt, bal in cur.fetchall():
        print(f"  {name[:38]:<38} {cnt:>3} inv  ${bal:>14,.2f}")

    section("AR Aging buckets")
    cur.execute("""SELECT aging_bucket, COUNT(*), ROUND(SUM(open_balance),2)
                   FROM v_ar_aging GROUP BY aging_bucket
                   ORDER BY CASE aging_bucket
                       WHEN 'Current' THEN 1 WHEN '1-30' THEN 2 WHEN '31-60' THEN 3
                       WHEN '61-90' THEN 4 WHEN '91-120' THEN 5 ELSE 6 END""")
    for bucket, cnt, amt in cur.fetchall():
        print(f"  {bucket:<10} {cnt:>4} inv  ${amt:>14,.2f}")

    print(f"\nDatabase written to: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
