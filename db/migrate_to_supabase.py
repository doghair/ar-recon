"""
Migrate data from local SQLite DB to Supabase via Management API.
Sends rows in batches to stay within API payload limits.
"""
import sqlite3, json, urllib.request, urllib.error
from pathlib import Path

REF   = "pikdtkqjhsektckwrkkb"
TOKEN = "sbp_488a6b2de39e11e6fa1fd59f1382d9727cbae73a"
URL   = f"https://api.supabase.com/v1/projects/{REF}/database/query"
DB    = Path(__file__).parent / "arrecon.db"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "curl/7.88.1",
    "Accept": "*/*",
}

def run_sql(sql):
    data = json.dumps({"query": sql}).encode()
    req = urllib.request.Request(URL, data=data, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"HTTP {e.code}: {body[:400]}")

def quote(v):
    """Escape a value for SQL insertion."""
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    # Escape single quotes
    return "'" + str(v).replace("'", "''") + "'"

def migrate_table(conn, table, pk_col, columns, batch=50):
    cur = conn.execute(f"SELECT {', '.join(columns)} FROM {table}")
    rows = cur.fetchall()
    print(f"  {table}: {len(rows)} rows", end="", flush=True)
    if not rows:
        print()
        return

    total = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i:i+batch]
        col_list = ", ".join(columns)
        values = []
        for row in chunk:
            vals = ", ".join(quote(v) for v in row)
            values.append(f"({vals})")
        sql = (
            f"INSERT INTO {table} ({col_list}) VALUES "
            + ",".join(values)
            + f" ON CONFLICT ({pk_col}) DO NOTHING"
        )
        run_sql(sql)
        total += len(chunk)
        print(f" {total}...", end="", flush=True)
    print(" done")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

tables = [
    ("customers", "customer_id", [
        "customer_id","customer_name","customer_type","city","state_country",
        "payment_terms","credit_limit","ap_email","ap_contact"
    ]),
    ("invoices", "invoice_id", [
        "invoice_id","customer_id","invoice_date","due_date","period",
        "product_id","product_description","product_category","quantity","unit_price",
        "gross_amount","discount_amount","net_amount","tax_amount","total_amount",
        "status","gl_entry_id","salesperson","territory","po_number","notes"
    ]),
    ("cash_receipts", "receipt_id", [
        "receipt_id","customer_id","receipt_date","amount","payment_method",
        "reference","check_number","invoice_id_applied","amount_applied",
        "bank_deposit_id","status","notes"
    ]),
    ("credit_memos", "memo_id", [
        "memo_id","customer_id","memo_date","period","amount","reason",
        "original_invoice_id","applied_to_invoice_id","gl_entry_id","status","notes"
    ]),
    ("gl_entries", "entry_id", [
        "entry_id","entry_date","period","account_code","account_name","entry_type",
        "debit","credit","description","source_doc","customer_id","posted_by","notes"
    ]),
    ("bank_statements", "line_id", [
        "line_id","bank_date","value_date","description","debit","credit",
        "deposit_id","transaction_type","matched_receipt_ids","reconciled","notes"
    ]),
    ("reconciliation_periods", "period", [
        "period","status","gl_balance","subledger_balance","variance",
        "reconciled_by","reconciled_at","locked_at","notes"
    ]),
]

print("Migrating data to Supabase...")
for table, pk, cols in tables:
    migrate_table(conn, table, pk, cols)

conn.close()

# Verify
print("\nVerifying row counts...")
for table, _, _ in tables:
    result = run_sql(f"SELECT COUNT(*) AS n FROM {table}")
    print(f"  {table}: {result[0]['n']} rows")

print("\nMigration complete!")
