"""
Generate historical AR data for 2024 and 2025.
Targets ~20% YoY revenue growth, anchored to actual 2026 Q1 monthly amounts.
Deletes any previous historical data before inserting fresh records.
"""
import os, random, sys
from datetime import date, timedelta
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

random.seed(42_2024)   # reproducible

# ── 2026 monthly invoice totals (Jan-Mar actuals, Apr-Dec estimated) ──────────
# Anchor: Q1 2026 actuals from live DB
#   Jan $16.87M, Feb $17.15M, Mar $15.94M → avg ~$16.65M/month
# Seasonal index (sums to 12.0 across all months):
#   Biotech pattern: soft Jan, strong Q2/Q4 close months
SEASONAL = {
     1: 0.88,   # Jan — slow start
     2: 0.93,   # Feb
     3: 1.06,   # Mar — Q1 push
     4: 0.96,   # Apr
     5: 1.00,   # May
     6: 1.14,   # Jun — H1 close
     7: 0.90,   # Jul — summer slow
     8: 0.95,   # Aug
     9: 1.08,   # Sep — Q3 push
    10: 1.09,   # Oct
    11: 1.00,   # Nov
    12: 1.21,   # Dec — year-end
}
# Annual target for 2026 = Q1 actual / (mean of Jan-Mar seasonal / 12)
# Q1 actual = $16.87M + $17.15M + $15.94M = $49.96M
# Q1 seasonal mean = (0.88 + 0.93 + 1.06) / 3 = 0.957
# Annual 2026 ≈ $49.96M / (0.957/12*3) ≈ $49.96M / 0.2393 ≈ $208.8M → use $205M for round numbers
ANNUAL_2026 = 205_000_000

# Override Jan-Mar with known actuals
MONTHLY_2026 = {}
for m, s in SEASONAL.items():
    MONTHLY_2026[m] = round(ANNUAL_2026 * s / 12)
# Actuals override
MONTHLY_2026[1] = 16_870_000
MONTHLY_2026[2] = 17_150_000
MONTHLY_2026[3] = 15_940_000

# 20% YoY: 2025 = 2026 / 1.20, 2024 = 2025 / 1.20
MONTHLY_TARGETS = {
    2025: {m: round(v / 1.20) for m, v in MONTHLY_2026.items()},
    2024: {m: round(v / 1.20 / 1.20) for m, v in MONTHLY_2026.items()},
}

print("Monthly revenue targets ($M):")
print(f"  {'Month':<8} {'2024':>10} {'2025':>10} {'2026':>10}")
for m in range(1, 13):
    print(f"  {m:02d}       {MONTHLY_TARGETS[2024][m]/1e6:>9.2f}  {MONTHLY_TARGETS[2025][m]/1e6:>9.2f}  {MONTHLY_2026[m]/1e6:>9.2f}")
print()

# ── Reference data ────────────────────────────────────────────────────────────

CUSTOMERS = [
    ("CUST-001","Hospital System","Net 30","Northeast",8),
    ("CUST-002","Hospital System","Net 30","Midwest",15),
    ("CUST-003","Hospital System","Net 30","Midwest",12),
    ("CUST-004","Hospital System","Net 30","Northeast",13),
    ("CUST-005","Hospital System","Net 30","West",9),
    ("CUST-006","Hospital System","Net 30","Northeast",8),
    ("CUST-007","Hospital System","Net 30","West",9),
    ("CUST-008","Hospital System","Net 30","Southeast",6),
    ("CUST-009","Hospital System","Net 30","Southeast",4),
    ("CUST-010","Hospital System","Net 30","West",7),
    ("CUST-011","Distributor","Net 45","Northeast",8),
    ("CUST-012","Distributor","Net 45","Southeast",18),
    ("CUST-013","Distributor","Net 45","Midwest",14),
    ("CUST-014","Distributor","Net 45","West",4),
    ("CUST-015","Distributor","Net 45","Northeast",6),
    ("CUST-017","Research Institution","Net 30","West",2),
    ("CUST-018","Research Institution","Net 30","Northeast",2),
    ("CUST-019","Research Institution","Net 30","West",3),
    ("CUST-020","Research Institution","Net 30","Northeast",3),
    ("CUST-021","Research Institution","Net 30","Southeast",3),
    ("CUST-022","Research Institution","Net 30","Northeast",5),
    ("CUST-023","GPO","Net 30","Midwest",7),
    ("CUST-024","GPO","Net 30","Southeast",4),
    ("CUST-025","GPO","Net 30","Northeast",5),
    ("CUST-026","Biotech","Net 30","West",3),
    ("CUST-027","Biotech","Net 30","Northeast",5),
    ("CUST-028","Biotech","Net 30","West",4),
    ("CUST-029","Biotech","Net 30","West",2),
    ("CUST-030","Biotech","Net 30","Northeast",3),
    ("CUST-031","CRO","Net 45","International",2),
    ("CUST-032","CRO","Net 45","Southeast",3),
    ("CUST-033","CRO","Net 45","Northeast",3),
    ("CUST-034","CDMO","Net 60","International",3),
    ("CUST-035","CDMO","Net 60","Southeast",2),
    ("CUST-036","Academic Medical","Net 30","Midwest",5),
    ("CUST-037","Academic Medical","Net 30","Northeast",7),
    ("CUST-038","Academic Medical","Net 30","West",4),
    ("CUST-039","Academic Medical","Net 30","West",2),
    ("CUST-041","Federal","Net 30","Northeast",2),
    ("CUST-043","Federal","Net 30","Southeast",1),
    ("CUST-044","International Pharma","Net 60","International",8),
    ("CUST-045","International Pharma","Net 60","International",10),
    ("CUST-046","International Pharma","Net 60","International",5),
    ("CUST-047","International Pharma","Net 60","International",4),
    ("CUST-048","Specialty Pharmacy","Net 30","Northeast",4),
    ("CUST-049","Specialty Pharmacy","Net 30","Midwest",2),
    ("CUST-051","Specialty Pharmacy","Net 30","West",1),
    ("CUST-053","Payer","Net 30","Midwest",2),
    ("CUST-054","Payer","Net 30","Northeast",2),
    ("CUST-055","Biotech","Net 30","Northeast",2),
    ("CUST-056","Biotech","Net 30","Northeast",2),
    ("CUST-057","Biotech","Net 30","Northeast",1),
    ("CUST-058","Biotech","Net 30","Northeast",1),
    ("CUST-059","Biotech","Net 30","Northeast",2),
    ("CUST-060","Biotech","Net 30","West",2),
]

CUST_IDS    = [c[0] for c in CUSTOMERS]
CUST_TERMS  = {c[0]: c[2] for c in CUSTOMERS}
CUST_TERR   = {c[0]: c[3] for c in CUSTOMERS}
CUST_WEIGHT = [c[4] for c in CUSTOMERS]
TERMS_DAYS  = {"Net 30": 30, "Net 45": 45, "Net 60": 60}

PRODUCTS = [
    ("PROD-001","NovaBio-Alpha 50mg Vial","Drug - Oncology",4200,4800,5,20,6),
    ("PROD-002","NovaBio-Alpha 100mg Vial","Drug - Oncology",8400,8600,5,20,8),
    ("PROD-003","CellFlex Reagent Kit","Research Reagent",1100,1350,10,50,10),
    ("PROD-004","GenomiX Sequencing Panel","Diagnostic",3900,4200,5,25,8),
    ("PROD-005","ImmunoBoost IV 200mg","Drug - Immunology",6100,6400,5,15,6),
    ("PROD-006","ProteaScreen Assay","Research Reagent",850,1100,10,50,8),
    ("PROD-007","NovaBio-Beta Infusion 500mg","Drug - Rare Disease",11000,13500,2,10,5),
    ("PROD-008","CytoGuard ELISA Kit","Diagnostic",720,870,10,40,7),
    ("PROD-009","BioTrack Monitoring Software (Annual)","Software",23000,26000,1,3,4),
    ("PROD-010","GeneTherapy Vector Lot","Cell & Gene Therapy",76000,84000,1,3,3),
    ("PROD-011","NovaBio-Gamma 250mg","Drug - Neurology",20000,24500,2,8,5),
    ("PROD-012","PharmaGrade Excipient Bulk","Raw Material",2800,3100,20,100,7),
    ("PROD-013","RegulatoryAI Platform License","Software",17000,19000,1,2,3),
    ("PROD-014","Clinical Trial Supply Kit","Clinical Supply",8900,9400,5,20,5),
    ("PROD-015","BioProcess Training Service","Professional Service",3600,4400,5,30,5),
]
PROD_WEIGHT = [p[7] for p in PRODUCTS]

TERRITORY_SALES = {
    "Northeast":    ["Tom Kane","Sara Hill"],
    "Southeast":    ["Brett Long"],
    "Midwest":      ["Sara Hill","Tom Kane"],
    "West":         ["Nadia Osei"],
    "International":["Yuki Tanaka"],
}
PAY_METHODS = ["ACH","ACH","ACH","Wire","Wire","EFT","EFT","EFT","Check","Check"]

# ── Counters ──────────────────────────────────────────────────────────────────
inv_seq  = 10000
rcp_seq  = 10000
gl_seq   = 10000
cm_seq   = 10000
bnk_seq  = 10000
dep_seq  = 100

def next_inv():  global inv_seq;  inv_seq  += 1; return f"INV-{inv_seq:05d}"
def next_rcp():  global rcp_seq;  rcp_seq  += 1; return f"RCP-{rcp_seq:05d}"
def next_gl():   global gl_seq;   gl_seq   += 1; return f"GL-{gl_seq:05d}"
def next_cm():   global cm_seq;   cm_seq   += 1; return f"CM-{cm_seq:05d}"
def next_bnk():  global bnk_seq;  bnk_seq  += 1; return f"BNK-{bnk_seq:05d}"
def next_dep():  global dep_seq;  dep_seq  += 1; return f"DEP-{dep_seq:04d}"

def r2(x): return round(x, 2)

def days_in_month(year, month):
    if month == 12: return (date(year + 1, 1, 1) - date(year, 12, 1)).days
    return (date(year, month + 1, 1) - date(year, month, 1)).days

def rand_date_in_month(year, month):
    d = days_in_month(year, month)
    return date(year, month, random.randint(1, d))

def insert_batch(table, rows, batch=50):
    for i in range(0, len(rows), batch):
        chunk = rows[i:i+batch]
        sb.table(table).insert(chunk).execute()
    print(f"  + {table}: {len(rows)} rows inserted")

# ── Delete previous historical data ──────────────────────────────────────────
def delete_historical():
    print("Deleting previous historical data...")
    # GL entries: by period (2024 and 2025 only)
    sb.table("gl_entries").delete().gte("period", "2024-01").lte("period", "2025-12").execute()
    # Credit memos: by date range
    sb.table("credit_memos").delete().gte("memo_date", "2024-01-01").lte("memo_date", "2025-12-31").execute()
    # Bank statements: by ID prefix
    sb.table("bank_statements").delete().gte("line_id", "BNK-10000").execute()
    # Cash receipts: by ID prefix
    sb.table("cash_receipts").delete().gte("receipt_id", "RCP-10000").execute()
    # Invoices: by ID prefix
    sb.table("invoices").delete().gte("invoice_id", "INV-10000").execute()
    print("  Done.\n")

# ── Generate one month of invoices, scaled to hit dollar target ───────────────
def gen_month_invoices(year, month, count, dollar_target):
    """
    Generate `count` invoices for the month, then proportionally scale each
    invoice's total_amount so the month sums exactly to dollar_target.
    """
    raw = []
    for _ in range(count):
        cust    = random.choices(CUST_IDS, weights=CUST_WEIGHT)[0]
        prod    = random.choices(PRODUCTS, weights=PROD_WEIGHT)[0]
        inv_id  = next_inv()
        inv_dt  = rand_date_in_month(year, month)
        terms   = CUST_TERMS[cust]
        due_dt  = inv_dt + timedelta(days=TERMS_DAYS[terms])
        period  = f"{year}-{month:02d}"

        unit_price = r2(random.uniform(prod[3], prod[4]))
        qty        = random.randint(prod[5], prod[6])
        gross      = r2(unit_price * qty)

        rand = random.random()
        if rand < 0.955:   status = "Paid"
        elif rand < 0.977: status = "Written Off"
        else:              status = "Short Pay - Open"

        terr   = CUST_TERR[cust]
        salesp = random.choice(TERRITORY_SALES.get(terr, TERRITORY_SALES["Northeast"]))
        po_num = f"PO-{random.randint(100000, 999999)}"

        raw.append({
            "invoice_id":          inv_id,
            "customer_id":         cust,
            "invoice_date":        inv_dt.isoformat(),
            "due_date":            due_dt.isoformat(),
            "period":              period,
            "product_id":          prod[0],
            "product_description": prod[1],
            "product_category":    prod[2],
            "quantity":            qty,
            "unit_price":          unit_price,
            "gross_amount":        gross,
            "discount_amount":     0,
            "net_amount":          gross,
            "tax_amount":          0,
            "total_amount":        gross,   # will be scaled below
            "status":              status,
            "gl_entry_id":         f"GL-INV-{inv_seq:05d}",
            "salesperson":         salesp,
            "territory":           terr,
            "po_number":           po_num,
            "notes":               None,
        })

    # Scale all amounts proportionally to hit the dollar target
    raw_total = sum(r["total_amount"] for r in raw)
    if raw_total > 0:
        scale = dollar_target / raw_total
        for r in raw:
            scaled = r2(r["total_amount"] * scale)
            r["total_amount"]  = scaled
            r["gross_amount"]  = scaled
            r["net_amount"]    = scaled
            r["unit_price"]    = r2(r["unit_price"] * scale)

    return raw

def gen_receipts(invoices):
    receipts = []
    for inv in invoices:
        if inv["status"] != "Paid":
            continue
        rcp_id  = next_rcp()
        inv_dt  = date.fromisoformat(inv["due_date"])
        lag     = random.randint(-5, 18)
        rcp_dt  = inv_dt + timedelta(days=max(0, lag))
        method  = random.choice(PAY_METHODS)
        ref     = f"REF-{random.randint(1000000, 9999999)}"
        chk     = f"CHK-{random.randint(10000, 99999)}" if method == "Check" else None

        receipts.append({
            "receipt_id":         rcp_id,
            "customer_id":        inv["customer_id"],
            "receipt_date":       rcp_dt.isoformat(),
            "amount":             inv["total_amount"],
            "payment_method":     method,
            "reference":          ref,
            "check_number":       chk,
            "invoice_id_applied": inv["invoice_id"],
            "amount_applied":     inv["total_amount"],
            "bank_deposit_id":    None,
            "status":             "Applied",
            "notes":              None,
        })
    return receipts

def assign_deposits(receipts):
    from collections import defaultdict
    by_week = defaultdict(list)
    for rcp in receipts:
        dt   = date.fromisoformat(rcp["receipt_date"])
        week = dt.isocalendar()[:2]
        by_week[week].append(rcp)
    for week_key, rcps in by_week.items():
        dep_id = next_dep()
        for rcp in rcps:
            rcp["bank_deposit_id"] = dep_id
    return receipts

def gen_gl_invoices(invoices):
    entries = []
    for inv in invoices:
        entries.append({
            "entry_id":    inv["gl_entry_id"],
            "entry_date":  inv["invoice_date"],
            "period":      inv["period"],
            "account_code":"1200",
            "account_name":"Accounts Receivable",
            "entry_type":  "AR",
            "debit":       inv["total_amount"],
            "credit":      0,
            "description": f"Invoice {inv['invoice_id']} - {inv['product_description']}",
            "source_doc":  inv["invoice_id"],
            "customer_id": inv["customer_id"],
            "posted_by":   "System",
            "notes":       None,
        })
    return entries

def gen_gl_receipts(receipts):
    entries = []
    for rcp in receipts:
        entries.append({
            "entry_id":    next_gl(),
            "entry_date":  rcp["receipt_date"],
            "period":      rcp["receipt_date"][:7],
            "account_code":"1000",
            "account_name":"Cash & Cash Equivalents",
            "entry_type":  "Cash",
            "debit":       rcp["amount"],
            "credit":      0,
            "description": f"Payment received - {rcp['receipt_id']} via {rcp['payment_method']}",
            "source_doc":  rcp["receipt_id"],
            "customer_id": rcp["customer_id"],
            "posted_by":   "System",
            "notes":       None,
        })
    return entries

def gen_bank_statements(receipts):
    from collections import defaultdict
    by_dep = defaultdict(list)
    for rcp in receipts:
        by_dep[rcp["bank_deposit_id"]].append(rcp)

    lines = []
    for dep_id, rcps in by_dep.items():
        total   = r2(sum(r["amount"] for r in rcps))
        dep_dt  = max(date.fromisoformat(r["receipt_date"]) for r in rcps)
        methods = list({r["payment_method"] for r in rcps})
        tx_type = methods[0] if len(methods) == 1 else "Mixed"

        lines.append({
            "line_id":             next_bnk(),
            "bank_date":           dep_dt.isoformat(),
            "value_date":          dep_dt.isoformat(),
            "description":         f"DEPOSIT {dep_id} - {tx_type} payment batch",
            "debit":               0,
            "credit":              total,
            "deposit_id":          dep_id,
            "transaction_type":    tx_type,
            "matched_receipt_ids": ",".join(r["receipt_id"] for r in rcps[:5]),
            "reconciled":          "Yes",
            "notes":               None,
        })
    return lines

def gen_credit_memos(all_invoices):
    memos    = []
    paid     = [i for i in all_invoices if i["status"] == "Paid"]
    n_memos  = max(1, int(len(paid) * 0.012))
    chosen   = random.sample(paid, n_memos)

    for inv in chosen:
        cm_id  = next_cm()
        inv_dt = date.fromisoformat(inv["invoice_date"])
        cm_dt  = inv_dt + timedelta(days=random.randint(15, 45))
        reason = random.choice([
            "Pricing Adjustment", "Damaged Goods Return", "Short Shipment",
            "Contractual Allowance", "Quality Issue Resolution",
        ])
        amt    = r2(inv["total_amount"] * random.uniform(0.02, 0.12))
        period = f"{cm_dt.year}-{cm_dt.month:02d}"

        memos.append({
            "memo_id":               cm_id,
            "customer_id":           inv["customer_id"],
            "memo_date":             cm_dt.isoformat(),
            "period":                period,
            "amount":                amt,
            "reason":                reason,
            "original_invoice_id":   inv["invoice_id"],
            "applied_to_invoice_id": inv["invoice_id"],
            "gl_entry_id":           next_gl(),
            "status":                "Applied",
            "notes":                 None,
        })
    return memos

# ── Generate one full year ────────────────────────────────────────────────────
def generate_year(year, base_invoices_per_month):
    print(f"\n-- Generating {year} data --")
    all_invoices = []
    all_receipts = []
    all_gl_inv   = []

    targets = MONTHLY_TARGETS[year]

    for month in range(1, 13):
        # ±10% invoice count variation; amounts are scaled to hit dollar target exactly
        count  = int(base_invoices_per_month * random.uniform(0.90, 1.10))
        target = targets[month]
        invs   = gen_month_invoices(year, month, count, target)
        rcps   = gen_receipts(invs)

        all_invoices.extend(invs)
        all_receipts.extend(rcps)
        all_gl_inv.extend(gen_gl_invoices(invs))

        actual = sum(i["total_amount"] for i in invs)
        print(f"  {year}-{month:02d}: {len(invs)} invoices  ${actual/1e6:.2f}M  (target ${target/1e6:.2f}M)")

    assign_deposits(all_receipts)
    all_gl_rcp = gen_gl_receipts(all_receipts)
    all_bank   = gen_bank_statements(all_receipts)
    all_memos  = gen_credit_memos(all_invoices)

    total_inv = r2(sum(i["total_amount"] for i in all_invoices))
    total_rcp = r2(sum(r["amount"]       for r in all_receipts))
    print(f"\n  Total invoiced:  ${total_inv/1e6:.2f}M  ({len(all_invoices)} invoices)")
    print(f"  Total collected: ${total_rcp/1e6:.2f}M  ({len(all_receipts)} receipts)")
    print(f"  Credit memos:    {len(all_memos)}")
    print(f"  Bank lines:      {len(all_bank)}")

    return all_invoices, all_receipts, all_gl_inv, all_gl_rcp, all_bank, all_memos

def insert_year(data, label):
    all_invoices, all_receipts, all_gl_inv, all_gl_rcp, all_bank, all_memos = data
    print(f"\n-- Inserting {label} into Supabase --")
    insert_batch("invoices",       all_invoices)
    insert_batch("cash_receipts",  all_receipts)
    insert_batch("gl_entries",     all_gl_inv + all_gl_rcp)
    if all_memos: insert_batch("credit_memos",  all_memos)
    if all_bank:  insert_batch("bank_statements", all_bank)

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    delete_historical()

    # 2024: ~72 invoices/month (10% fewer than 2025, amounts scaled to target)
    data_2024 = generate_year(2024, base_invoices_per_month=72)
    insert_year(data_2024, "2024")

    # 2025: ~80 invoices/month (amounts scaled to target)
    data_2025 = generate_year(2025, base_invoices_per_month=80)
    insert_year(data_2025, "2025")

    print("\nDone! 2024 and 2025 data reloaded.")
