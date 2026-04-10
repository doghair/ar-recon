import csv
import random
from datetime import date, timedelta
from decimal import Decimal

random.seed(42)

# ── helpers ──────────────────────────────────────────────────────────────────
def rand_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def fmt(d): return d.strftime("%Y-%m-%d")

def r(lo, hi, step=0.01):
    return round(random.uniform(lo, hi) / step) * step

# ── 1. CUSTOMERS ─────────────────────────────────────────────────────────────
customers = [
    # Hospital systems
    ("CUST-001","Johns Hopkins Health System","Hospital System","Baltimore","MD","Net 30",5000000,"accounts.payable@jhu.edu","Emily Hartman"),
    ("CUST-002","Mayo Clinic","Hospital System","Rochester","MN","Net 45",8000000,"ap@mayo.edu","Tom Brody"),
    ("CUST-003","Cleveland Clinic","Hospital System","Cleveland","OH","Net 30",6000000,"ap@ccf.org","Sandra Lee"),
    ("CUST-004","Mass General Brigham","Hospital System","Boston","MA","Net 45",7500000,"payables@mgb.org","Kevin Walsh"),
    ("CUST-005","UCSF Medical Center","Hospital System","San Francisco","CA","Net 30",4000000,"ap@ucsf.edu","Rachel Kim"),
    ("CUST-006","NYU Langone Health","Hospital System","New York","NY","Net 30",4500000,"ap@nyulangone.org","James Denton"),
    ("CUST-007","Cedars-Sinai Medical Center","Hospital System","Los Angeles","CA","Net 45",3500000,"ap@csmc.edu","Patricia Olsen"),
    ("CUST-008","Duke University Hospital","Hospital System","Durham","NC","Net 30",3000000,"ap@duke.edu","Mark Finley"),
    ("CUST-009","Vanderbilt University Medical Center","Hospital System","Nashville","TN","Net 30",2500000,"ap@vumc.org","Susan Park"),
    ("CUST-010","Stanford Health Care","Hospital System","Palo Alto","CA","Net 45",4000000,"ap@stanfordhealthcare.org","Brian Torres"),
    # Specialty Distributors
    ("CUST-011","McKesson Specialty Health","Distributor","The Woodlands","TX","Net 30",10000000,"ar.disputes@mckesson.com","David Nguyen"),
    ("CUST-012","AmerisourceBergen Specialty","Distributor","Conshohocken","PA","Net 30",10000000,"payments@amerisourcebergen.com","Gina Flores"),
    ("CUST-013","Cardinal Health Specialty","Distributor","Dublin","OH","Net 30",9000000,"ap@cardinalhealth.com","Frank Russo"),
    ("CUST-014","Biologics Inc.","Distributor","Morrisville","NC","Net 45",2000000,"invoices@biologicsinc.com","Heather Brooks"),
    ("CUST-015","Diplomat Specialty Pharmacy","Distributor","Flint","MI","Net 30",1500000,"ap@diplomat.com","Nathan Cole"),
    # Research Institutions
    ("CUST-016","Broad Institute","Research Institution","Cambridge","MA","Net 45",1000000,"ap@broadinstitute.org","Olivia Grant"),
    ("CUST-017","Salk Institute for Biological Studies","Research Institution","La Jolla","CA","Net 45",800000,"purchasing@salk.edu","Carlos Mendez"),
    ("CUST-018","Whitehead Institute","Research Institution","Cambridge","MA","Net 30",500000,"accounts@wi.mit.edu","Diana Shah"),
    ("CUST-019","Fred Hutchinson Cancer Center","Research Institution","Seattle","WA","Net 45",1200000,"ap@fredhutch.org","Aaron Patel"),
    ("CUST-020","Dana-Farber Cancer Institute","Research Institution","Boston","MA","Net 30",1500000,"ap@dfci.harvard.edu","Laura Green"),
    ("CUST-021","MD Anderson Cancer Center","Research Institution","Houston","TX","Net 30",2000000,"ap@mdanderson.org","Steven Clark"),
    ("CUST-022","Memorial Sloan Kettering","Research Institution","New York","NY","Net 45",2500000,"ap@mskcc.org","Tina Murphy"),
    # GPOs
    ("CUST-023","Vizient Inc.","GPO","Irving","TX","Net 30",5000000,"ap@vizientinc.com","Paul Adams"),
    ("CUST-024","Premier Inc.","GPO","Charlotte","NC","Net 30",4000000,"payables@premierinc.com","Lisa Jordan"),
    ("CUST-025","HealthTrust Performance Group","GPO","Nashville","TN","Net 30",3000000,"ap@healthtrustpg.com","Robert Kim"),
    # Biotech / Pharma
    ("CUST-026","Genentech Inc.","Biotech","South San Francisco","CA","Net 45",3000000,"ap@gene.com","Jennifer Wu"),
    ("CUST-027","Regeneron Pharmaceuticals","Biotech","Tarrytown","NY","Net 45",2500000,"ap@regeneron.com","Michael Young"),
    ("CUST-028","BioMarin Pharmaceutical","Biotech","San Rafael","CA","Net 30",1000000,"ap@biomarin.com","Amy Chen"),
    ("CUST-029","Ultragenyx Pharmaceutical","Biotech","Novato","CA","Net 45",800000,"ap@ultragenyx.com","Daniel Morris"),
    ("CUST-030","Blueprint Medicines","Biotech","Cambridge","MA","Net 30",700000,"ap@blueprintmedicines.com","Stephanie Hall"),
    # CROs / CDMOs
    ("CUST-031","ICON plc","CRO","Dublin","IRE","Net 45",500000,"ap@iconplc.com","Chris Bennett"),
    ("CUST-032","PPD (Thermo Fisher)","CRO","Wilmington","NC","Net 45",600000,"ap@ppd.com","Megan Foster"),
    ("CUST-033","Parexel International","CRO","Waltham","MA","Net 30",400000,"ap@parexel.com","Ryan Dixon"),
    ("CUST-034","Lonza Group","CDMO","Basel","CH","Net 60",900000,"ap@lonza.com","Karen Simmons"),
    ("CUST-035","Patheon (Thermo Fisher)","CDMO","Durham","NC","Net 45",700000,"ap@patheon.com","Gary Newton"),
    # Academic Medical Centers
    ("CUST-036","University of Michigan Health","Academic Medical","Ann Arbor","MI","Net 30",2000000,"ap@med.umich.edu","Alice Roberts"),
    ("CUST-037","University of Pittsburgh Medical","Academic Medical","Pittsburgh","PA","Net 30",1800000,"ap@upmc.edu","Brandon Scott"),
    ("CUST-038","UC San Diego Health","Academic Medical","San Diego","CA","Net 45",1500000,"ap@health.ucsd.edu","Catherine Price"),
    ("CUST-039","University of Washington Medical","Academic Medical","Seattle","WA","Net 30",1200000,"ap@uwmedicine.org","Derek Evans"),
    ("CUST-040","Emory Healthcare","Academic Medical","Atlanta","GA","Net 30",2200000,"ap@emory.edu","Elaine Turner"),
    # Federal / Government
    ("CUST-041","NIH Clinical Center","Federal","Bethesda","MD","Net 30",500000,"ap@nih.gov","Frank White"),
    ("CUST-042","Veterans Health Administration","Federal","Washington","DC","Net 30",800000,"ap@va.gov","Gloria Harris"),
    ("CUST-043","Department of Defense Health","Federal","Washington","DC","Net 45",600000,"ap@health.mil","Henry Johnson"),
    # International
    ("CUST-044","Roche (Basel HQ)","International Pharma","Basel","CH","Net 60",3500000,"ap@roche.com","Isabelle Dupont"),
    ("CUST-045","Novartis AG","International Pharma","Basel","CH","Net 60",3000000,"ap@novartis.com","Jean-Pierre Moreau"),
    ("CUST-046","AstraZeneca UK","International Pharma","Cambridge","UK","Net 60",2500000,"ap@astrazeneca.com","Katherine Smith"),
    ("CUST-047","UCB Pharma","International Pharma","Brussels","BE","Net 60",1000000,"ap@ucb.com","Luc Vandenberg"),
    # Specialty Pharmacy
    ("CUST-048","CVS Specialty","Specialty Pharmacy","Woonsocket","RI","Net 30",2000000,"ap@cvsspecialty.com","Mary Collins"),
    ("CUST-049","Walgreens Specialty","Specialty Pharmacy","Deerfield","IL","Net 30",1800000,"ap@walgreens.com","Nicholas Ward"),
    ("CUST-050","Accredo Health Group","Specialty Pharmacy","Memphis","TN","Net 30",1500000,"ap@accredo.com","Olivia Powell"),
    ("CUST-051","Coram CVS Specialty","Specialty Pharmacy","Denver","CO","Net 30",900000,"ap@coram.com","Peter Hughes"),
    ("CUST-052","AllianceRx Walgreens Prime","Specialty Pharmacy","Pittsburgh","PA","Net 30",800000,"ap@alliancerx.com","Quinn Barnes"),
    # Payers / Managed Care
    ("CUST-053","UnitedHealth Group","Payer","Minnetonka","MN","Net 45",1000000,"ap@uhg.com","Rebecca Foster"),
    ("CUST-054","Cigna Health","Payer","Bloomfield","CT","Net 45",800000,"ap@cigna.com","Samuel Cook"),
    # Additional Biotech
    ("CUST-055","Agios Pharmaceuticals","Biotech","Cambridge","MA","Net 30",400000,"ap@agios.com","Tamara Bell"),
    ("CUST-056","Alnylam Pharmaceuticals","Biotech","Cambridge","MA","Net 45",600000,"ap@alnylam.com","Victor Gray"),
    ("CUST-057","Bluebird Bio","Biotech","Somerville","MA","Net 30",300000,"ap@bluebirdbio.com","Wendy Hayes"),
    ("CUST-058","Sage Therapeutics","Biotech","Cambridge","MA","Net 30",350000,"ap@sagerx.com","Xavier Long"),
    ("CUST-059","Karuna Therapeutics","Biotech","Boston","MA","Net 45",250000,"ap@karunatx.com","Yolanda Price"),
    ("CUST-060","Relay Therapeutics","Biotech","Cambridge","MA","Net 30",200000,"ap@relaytx.com","Zachary Reed"),
]

# ── Write customers.csv ───────────────────────────────────────────────────────
with open("customers.csv","w",newline="") as f:
    w = csv.writer(f)
    w.writerow(["customer_id","customer_name","customer_type","city","state_country",
                "payment_terms","credit_limit","ap_email","ap_contact"])
    w.writerows(customers)
print("customers.csv written:", len(customers), "rows")

# ── Build invoice data ────────────────────────────────────────────────────────
# Product catalogue
products = [
    ("PROD-001","NovaBio-Alpha 50mg Vial",4500,"Drug - Oncology"),
    ("PROD-002","NovaBio-Alpha 100mg Vial",8200,"Drug - Oncology"),
    ("PROD-003","CellFlex Reagent Kit",1200,"Research Reagent"),
    ("PROD-004","GenomiX Sequencing Panel",3800,"Diagnostic"),
    ("PROD-005","ImmunoBoost IV 200mg",6500,"Drug - Immunology"),
    ("PROD-006","ProteaScreen Assay",950,"Research Reagent"),
    ("PROD-007","NovaBio-Beta Infusion 500mg",12000,"Drug - Rare Disease"),
    ("PROD-008","CytoGuard ELISA Kit",780,"Diagnostic"),
    ("PROD-009","BioTrack Monitoring Software (Annual)",25000,"Software"),
    ("PROD-010","GeneTherapy Vector Lot",85000,"Cell & Gene Therapy"),
    ("PROD-011","NovaBio-Gamma 250mg",22000,"Drug - Neurology"),
    ("PROD-012","PharmaGrade Excipient Bulk",3200,"Raw Material"),
    ("PROD-013","RegulatoryAI Platform License",18000,"Software"),
    ("PROD-014","Clinical Trial Supply Kit",9500,"Clinical Supply"),
    ("PROD-015","BioProcess Training Service",4000,"Professional Service"),
]

# period: Jan–Mar 2026 (current = 2026-04-09, so Q1 is the reconciliation period)
PERIODS = [
    (date(2026,1,1), date(2026,1,31), "2026-01"),
    (date(2026,2,1), date(2026,2,28), "2026-02"),
    (date(2026,3,1), date(2026,3,31), "2026-03"),
]

TARGET_MONTHLY = 20_000_000
invoices_out = []
inv_id = 1

# Monthly invoice budget allocation by customer weight
cust_ids = [c[0] for c in customers]
weights = [c[6] for c in customers]  # credit_limit as proxy for revenue share
total_w = sum(weights)

for p_start, p_end, period_label in PERIODS:
    monthly_budget = TARGET_MONTHLY
    allocated = 0
    for i, cust in enumerate(customers):
        cust_id = cust[0]
        terms = cust[5]
        due_days = int(terms.split()[1])
        share = (weights[i] / total_w) * monthly_budget
        # number of invoices for this customer this month
        n_inv = max(1, int(share / random.uniform(50000, 300000)))
        remaining = share
        for j in range(n_inv):
            if remaining <= 0:
                break
            prod = random.choice(products)
            qty = random.randint(1, max(1, int(remaining / prod[2])))
            qty = min(qty, 500)
            unit_price = prod[2] * random.uniform(0.9, 1.15)
            amount = round(qty * unit_price, 2)
            if amount > remaining * 1.1:
                amount = round(remaining, 2)
            if amount <= 0:
                break
            remaining -= amount
            allocated += amount

            inv_date = rand_date(p_start, p_end)
            due_date = inv_date + timedelta(days=due_days)
            inv_num = f"INV-{inv_id:05d}"

            invoices_out.append({
                "invoice_id": inv_num,
                "customer_id": cust_id,
                "invoice_date": fmt(inv_date),
                "due_date": fmt(due_date),
                "period": period_label,
                "product_id": prod[0],
                "product_description": prod[1],
                "product_category": prod[3],
                "quantity": qty,
                "unit_price": round(unit_price, 2),
                "gross_amount": amount,
                "discount_amount": 0.0,
                "net_amount": amount,
                "tax_amount": 0.0,
                "total_amount": amount,
                "status": "Open",       # will update below
                "gl_entry_id": f"GL-INV-{inv_id:05d}",
                "salesperson": random.choice(["Sara Hill","Tom Kane","Nadia Osei","Brett Long","Yuki Tanaka"]),
                "territory": random.choice(["Northeast","Southeast","Midwest","West","International"]),
                "po_number": f"PO-{random.randint(100000,999999)}",
                "notes": "",
            })
            inv_id += 1

print(f"Invoices generated: {len(invoices_out)}")

# ── Inject reconciliation scenarios ──────────────────────────────────────────
# We'll track scenario flags for GL generation
scenario_flags = {}   # inv_id -> scenario

# Scenario 1: Invoice in subledger MISSING from GL (2 invoices – mark gl_entry_id as None)
missing_gl = [invoices_out[10]["invoice_id"], invoices_out[55]["invoice_id"]]
for inv in invoices_out:
    if inv["invoice_id"] in missing_gl:
        inv["gl_entry_id"] = None
        inv["notes"] = "SCENARIO: subledger entry exists; GL posting missing"

# Scenario 2: Duplicate invoice in GL (1 invoice gets a dup flag)
dup_inv = invoices_out[22]["invoice_id"]
invoices_out[22]["notes"] = "SCENARIO: GL has duplicate posting for this invoice"

# Scenario 3: Short pay – these invoices will have partial payments
short_pay_ids = [invoices_out[30]["invoice_id"], invoices_out[80]["invoice_id"],
                 invoices_out[120]["invoice_id"], invoices_out[200]["invoice_id"]]

# Scenario 4: Write-off (2 invoices)
write_off_ids = [invoices_out[15]["invoice_id"], invoices_out[95]["invoice_id"]]
for inv in invoices_out:
    if inv["invoice_id"] in write_off_ids:
        inv["status"] = "Written Off"
        inv["notes"] = "SCENARIO: Written off in GL; subledger not updated"

print("Scenarios injected into invoices")

# ── Cash Receipts ─────────────────────────────────────────────────────────────
receipts = []
receipt_id = 1
deposit_id = 1
deposit_map = {}  # date -> deposit_id

unapplied_cash_invoices = [invoices_out[40]["invoice_id"], invoices_out[75]["invoice_id"],
                            invoices_out[130]["invoice_id"]]

# also collect timing diff invoices (paid on 3/31 but posted 4/1 - handle in bank statements)
timing_diff_invoices = [invoices_out[5]["invoice_id"], invoices_out[60]["invoice_id"],
                        invoices_out[110]["invoice_id"], invoices_out[160]["invoice_id"]]

def get_deposit_id(pay_date):
    global deposit_id
    if pay_date not in deposit_map:
        deposit_map[pay_date] = f"DEP-{deposit_id:04d}"
        deposit_id += 1
    return deposit_map[pay_date]

credit_memo_ids_by_inv = {}  # invoice_id -> credit_memo

for inv in invoices_out:
    inv_amount = inv["total_amount"]
    inv_date = date.fromisoformat(inv["invoice_date"])
    due_date = date.fromisoformat(inv["due_date"])
    cust = next(c for c in customers if c[0] == inv["customer_id"])
    terms_days = int(cust[5].split()[1])

    if inv["status"] == "Written Off":
        # No cash receipt for written-off invoices
        inv["status"] = "Written Off"
        continue

    # Unapplied cash: receipt recorded but not matched to invoice
    if inv["invoice_id"] in unapplied_cash_invoices:
        pay_date = rand_date(due_date, due_date + timedelta(days=10))
        dep = get_deposit_id(fmt(pay_date))
        receipts.append({
            "receipt_id": f"RCP-{receipt_id:05d}",
            "customer_id": inv["customer_id"],
            "receipt_date": fmt(pay_date),
            "amount": inv_amount,
            "payment_method": random.choice(["ACH","Wire","Check"]),
            "reference": f"REF-{random.randint(1000000,9999999)}",
            "check_number": f"CHK-{random.randint(10000,99999)}" if random.random()>0.5 else "",
            "invoice_id_applied": "",   # UNAPPLIED
            "amount_applied": 0.0,
            "bank_deposit_id": dep,
            "status": "Unapplied",
            "notes": "SCENARIO: Cash received; not applied to invoice",
        })
        inv["status"] = "Open"   # invoice remains open
        receipt_id += 1
        continue

    # Short pay
    if inv["invoice_id"] in short_pay_ids:
        short_pct = random.uniform(0.88, 0.97)
        pay_amt = round(inv_amount * short_pct, 2)
        pay_date = rand_date(due_date - timedelta(days=5), due_date + timedelta(days=15))
        dep = get_deposit_id(fmt(pay_date))
        receipts.append({
            "receipt_id": f"RCP-{receipt_id:05d}",
            "customer_id": inv["customer_id"],
            "receipt_date": fmt(pay_date),
            "amount": pay_amt,
            "payment_method": random.choice(["ACH","Wire"]),
            "reference": f"REF-{random.randint(1000000,9999999)}",
            "check_number": "",
            "invoice_id_applied": inv["invoice_id"],
            "amount_applied": pay_amt,
            "bank_deposit_id": dep,
            "status": "Applied",
            "notes": f"SCENARIO: Short pay; underpaid by {round(inv_amount-pay_amt,2)}",
        })
        inv["status"] = "Short Pay - Open"
        inv["notes"] = f"SCENARIO: Short pay; balance due {round(inv_amount-pay_amt,2)}"
        receipt_id += 1
        continue

    # Timing difference invoices (payment date = 3/31 but we'll post bank on 4/1)
    if inv["invoice_id"] in timing_diff_invoices:
        pay_date = date(2026,3,31)
        dep = get_deposit_id(fmt(pay_date))
        receipts.append({
            "receipt_id": f"RCP-{receipt_id:05d}",
            "customer_id": inv["customer_id"],
            "receipt_date": fmt(pay_date),
            "amount": inv_amount,
            "payment_method": "Wire",
            "reference": f"REF-{random.randint(1000000,9999999)}",
            "check_number": "",
            "invoice_id_applied": inv["invoice_id"],
            "amount_applied": inv_amount,
            "bank_deposit_id": dep,
            "status": "Applied",
            "notes": "SCENARIO: Timing diff – receipt posted 3/31, bank deposit 4/1",
        })
        inv["status"] = "Paid"
        receipt_id += 1
        continue

    # Determine if invoice is paid by now (2026-04-09)
    # ~85% of due invoices get paid within 15 days of due date
    paid_prob = 0.92 if due_date < date(2026,3,15) else (0.70 if due_date < date(2026,4,1) else 0.30)
    if random.random() < paid_prob:
        pay_lag = random.randint(0, 18)
        pay_date = due_date + timedelta(days=pay_lag)
        if pay_date > date(2026,4,9):
            pay_date = date(2026,4,9)
        dep = get_deposit_id(fmt(pay_date))
        receipts.append({
            "receipt_id": f"RCP-{receipt_id:05d}",
            "customer_id": inv["customer_id"],
            "receipt_date": fmt(pay_date),
            "amount": inv_amount,
            "payment_method": random.choice(["ACH","Wire","Check","EFT"]),
            "reference": f"REF-{random.randint(1000000,9999999)}",
            "check_number": f"CHK-{random.randint(10000,99999)}" if random.random()>0.6 else "",
            "invoice_id_applied": inv["invoice_id"],
            "amount_applied": inv_amount,
            "bank_deposit_id": dep,
            "status": "Applied",
            "notes": "",
        })
        inv["status"] = "Paid"
        receipt_id += 1
    # else stays Open

print(f"Cash receipts: {len(receipts)}")

# ── Credit Memos ──────────────────────────────────────────────────────────────
credit_memos = []
cm_id = 1
# Pick ~40 paid invoices for credit memo (returns, price adjustments)
paid_invs = [i for i in invoices_out if i["status"]=="Paid"]
cm_sample = random.sample(paid_invs, 40)

unapplied_cm_ids = set()
# 3 credit memos NOT applied to open invoices (scenario)
unapplied_cm_sample = random.sample(cm_sample[:15], 3)
for inv in unapplied_cm_sample:
    unapplied_cm_ids.add(inv["invoice_id"])

for inv in cm_sample:
    cm_pct = random.uniform(0.05, 0.25)
    cm_amt = round(inv["total_amount"] * cm_pct, 2)
    cm_date = date.fromisoformat(inv["invoice_date"]) + timedelta(days=random.randint(5,30))
    reason = random.choice(["Product Return","Pricing Adjustment","Damaged Goods",
                             "Quantity Dispute","Contract Rebate","Early Pay Discount"])
    applied = inv["invoice_id"] if inv["invoice_id"] not in unapplied_cm_ids else ""
    note = "" if applied else "SCENARIO: Credit memo issued; not applied to open invoice"
    credit_memos.append({
        "memo_id": f"CM-{cm_id:04d}",
        "customer_id": inv["customer_id"],
        "memo_date": fmt(cm_date),
        "period": inv["period"],
        "amount": cm_amt,
        "reason": reason,
        "original_invoice_id": inv["invoice_id"],
        "applied_to_invoice_id": applied,
        "gl_entry_id": f"GL-CM-{cm_id:04d}",
        "status": "Applied" if applied else "Unapplied",
        "notes": note,
    })
    cm_id += 1

print(f"Credit memos: {len(credit_memos)}")

# ── GL Entries ────────────────────────────────────────────────────────────────
gl_entries = []
gl_id = 1

def gl(entry_id, gl_date, period, account_code, account_name, entry_type,
       debit, credit, description, source_doc, customer_id="", notes=""):
    return {
        "entry_id": entry_id,
        "entry_date": fmt(gl_date) if not isinstance(gl_date, str) else gl_date,
        "period": period,
        "account_code": account_code,
        "account_name": account_name,
        "entry_type": entry_type,
        "debit": round(debit, 2),
        "credit": round(credit, 2),
        "description": description,
        "source_doc": source_doc,
        "customer_id": customer_id,
        "posted_by": random.choice(["jsmith","kchan","mlopez","arogers","tbrown"]),
        "notes": notes,
    }

# Invoice entries (AR Dr / Revenue Cr)
for inv in invoices_out:
    if inv["gl_entry_id"] is None:
        continue   # missing GL scenario – skip
    gl_date = date.fromisoformat(inv["invoice_date"])
    period = inv["period"]
    amt = inv["total_amount"]
    gl_entries.append(gl(f"GL-{gl_id:06d}", gl_date, period,
        "1200","Accounts Receivable","Invoice",
        amt, 0, f"Invoice {inv['invoice_id']} – {inv['customer_id']}",
        inv["invoice_id"], inv["customer_id"]))
    gl_id += 1
    gl_entries.append(gl(f"GL-{gl_id:06d}", gl_date, period,
        "4000","Revenue – Product Sales","Invoice",
        0, amt, f"Revenue recognition {inv['invoice_id']}",
        inv["invoice_id"], inv["customer_id"]))
    gl_id += 1
    # Duplicate GL scenario
    if inv["invoice_id"] == dup_inv:
        gl_entries.append(gl(f"GL-{gl_id:06d}", gl_date, period,
            "1200","Accounts Receivable","Invoice - DUPLICATE",
            amt, 0, f"DUPLICATE POSTING {inv['invoice_id']}",
            inv["invoice_id"], inv["customer_id"],
            notes="SCENARIO: Duplicate GL posting"))
        gl_id += 1
        gl_entries.append(gl(f"GL-{gl_id:06d}", gl_date, period,
            "4000","Revenue – Product Sales","Invoice - DUPLICATE",
            0, amt, f"DUPLICATE Revenue {inv['invoice_id']}",
            inv["invoice_id"], inv["customer_id"],
            notes="SCENARIO: Duplicate GL posting"))
        gl_id += 1

# Cash receipt entries (Cash Dr / AR Cr)
for rcp in receipts:
    rcp_date = date.fromisoformat(rcp["receipt_date"])
    period_label = rcp_date.strftime("%Y-%m")
    amt = rcp["amount"]
    gl_entries.append(gl(f"GL-{gl_id:06d}", rcp_date, period_label,
        "1000","Cash – Operating Account","Cash Receipt",
        amt, 0, f"Payment received {rcp['receipt_id']} – {rcp['customer_id']}",
        rcp["receipt_id"], rcp["customer_id"]))
    gl_id += 1
    if rcp["status"] == "Applied":
        gl_entries.append(gl(f"GL-{gl_id:06d}", rcp_date, period_label,
            "1200","Accounts Receivable","Cash Receipt",
            0, amt, f"AR cleared {rcp['receipt_id']} against {rcp['invoice_id_applied']}",
            rcp["receipt_id"], rcp["customer_id"]))
        gl_id += 1
    else:
        # Unapplied cash – credit to suspense
        gl_entries.append(gl(f"GL-{gl_id:06d}", rcp_date, period_label,
            "2050","Customer Deposits – Suspense","Unapplied Cash",
            0, amt, f"Unapplied cash {rcp['receipt_id']} – held in suspense",
            rcp["receipt_id"], rcp["customer_id"],
            notes="SCENARIO: Unapplied – not cleared against AR"))
        gl_id += 1

# Credit memo entries (Revenue Dr / AR Cr)
for cm in credit_memos:
    cm_date = date.fromisoformat(cm["memo_date"])
    period_label = cm_date.strftime("%Y-%m")
    amt = cm["amount"]
    gl_entries.append(gl(f"GL-{gl_id:06d}", cm_date, period_label,
        "4000","Revenue – Product Sales","Credit Memo",
        amt, 0, f"Credit memo {cm['memo_id']} – {cm['reason']}",
        cm["memo_id"], cm["customer_id"]))
    gl_id += 1
    gl_entries.append(gl(f"GL-{gl_id:06d}", cm_date, period_label,
        "1200","Accounts Receivable","Credit Memo",
        0, amt, f"AR credit {cm['memo_id']} against {cm['original_invoice_id']}",
        cm["memo_id"], cm["customer_id"]))
    gl_id += 1

# Write-off entries (Bad Debt Dr / AR Cr)
for inv in invoices_out:
    if inv["status"] != "Written Off":
        continue
    wo_date = date(2026, 3, 31)
    amt = inv["total_amount"]
    gl_entries.append(gl(f"GL-{gl_id:06d}", wo_date, "2026-03",
        "5500","Bad Debt Expense","Write-Off",
        amt, 0, f"Write-off approved – {inv['invoice_id']} {inv['customer_id']}",
        inv["invoice_id"], inv["customer_id"],
        notes="SCENARIO: GL write-off; subledger status not updated"))
    gl_id += 1
    gl_entries.append(gl(f"GL-{gl_id:06d}", wo_date, "2026-03",
        "1200","Accounts Receivable","Write-Off",
        0, amt, f"AR cleared via write-off {inv['invoice_id']}",
        inv["invoice_id"], inv["customer_id"],
        notes="SCENARIO: GL write-off; subledger status not updated"))
    gl_id += 1

print(f"GL entries: {len(gl_entries)}")

# ── Bank Statements ────────────────────────────────────────────────────────────
bank_lines = []
bline_id = 1

# Group receipts by deposit_id
from collections import defaultdict
dep_groups = defaultdict(list)
for rcp in receipts:
    dep_groups[rcp["bank_deposit_id"]].append(rcp)

for dep, dep_receipts in dep_groups.items():
    total = round(sum(r["amount"] for r in dep_receipts), 2)
    dep_date_str = dep_receipts[0]["receipt_date"]
    dep_date = date.fromisoformat(dep_date_str)

    # Timing difference: 4 deposits dated 3/31 show on bank as 4/1
    is_timing = dep_date == date(2026,3,31) and any(r["invoice_id_applied"] in timing_diff_invoices
                                                     for r in dep_receipts
                                                     if "invoice_id_applied" in r)
    bank_date = date(2026,4,1) if is_timing else dep_date
    note = "SCENARIO: Timing diff – receipt 3/31, bank clears 4/1" if is_timing else ""

    bank_lines.append({
        "line_id": f"BNK-{bline_id:05d}",
        "bank_date": fmt(bank_date),
        "value_date": fmt(dep_date),
        "description": f"Deposit {dep} – {len(dep_receipts)} item(s)",
        "debit": 0.0,
        "credit": total,
        "deposit_id": dep,
        "transaction_type": "Deposit",
        "matched_receipt_ids": "|".join(r["receipt_id"] for r in dep_receipts),
        "reconciled": "No" if is_timing else "Yes",
        "notes": note,
    })
    bline_id += 1

# Add bank fees, service charges, and wire fees (debits)
bank_service_dates = [date(2026,1,31), date(2026,2,28), date(2026,3,31)]
for d in bank_service_dates:
    bank_lines.append({
        "line_id": f"BNK-{bline_id:05d}",
        "bank_date": fmt(d),
        "value_date": fmt(d),
        "description": "Monthly Service Charge",
        "debit": 450.00,
        "credit": 0.0,
        "deposit_id": "",
        "transaction_type": "Bank Fee",
        "matched_receipt_ids": "",
        "reconciled": "No",
        "notes": "Bank service fee – needs GL entry",
    })
    bline_id += 1
    for _ in range(random.randint(5,12)):
        fee_date = rand_date(d.replace(day=1), d)
        bank_lines.append({
            "line_id": f"BNK-{bline_id:05d}",
            "bank_date": fmt(fee_date),
            "value_date": fmt(fee_date),
            "description": f"Wire Transfer Fee",
            "debit": random.choice([15, 25, 35, 50]),
            "credit": 0.0,
            "deposit_id": "",
            "transaction_type": "Wire Fee",
            "matched_receipt_ids": "",
            "reconciled": "No",
            "notes": "Wire fee – needs GL entry",
        })
        bline_id += 1

# Sort by date
bank_lines.sort(key=lambda x: x["bank_date"])
print(f"Bank statement lines: {len(bank_lines)}")

# ── Write all CSVs ────────────────────────────────────────────────────────────
def write_csv(filename, rows, fieldnames):
    with open(filename, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  {filename}: {len(rows)} rows")

print("\nWriting CSVs...")
write_csv("invoices.csv", invoices_out, [
    "invoice_id","customer_id","invoice_date","due_date","period","product_id",
    "product_description","product_category","quantity","unit_price","gross_amount",
    "discount_amount","net_amount","tax_amount","total_amount","status",
    "gl_entry_id","salesperson","territory","po_number","notes"])

write_csv("cash_receipts.csv", receipts, [
    "receipt_id","customer_id","receipt_date","amount","payment_method",
    "reference","check_number","invoice_id_applied","amount_applied",
    "bank_deposit_id","status","notes"])

write_csv("credit_memos.csv", credit_memos, [
    "memo_id","customer_id","memo_date","period","amount","reason",
    "original_invoice_id","applied_to_invoice_id","gl_entry_id","status","notes"])

write_csv("gl_entries.csv", gl_entries, [
    "entry_id","entry_date","period","account_code","account_name","entry_type",
    "debit","credit","description","source_doc","customer_id","posted_by","notes"])

write_csv("bank_statements.csv", bank_lines, [
    "line_id","bank_date","value_date","description","debit","credit",
    "deposit_id","transaction_type","matched_receipt_ids","reconciled","notes"])

# ── Summary ───────────────────────────────────────────────────────────────────
total_invoiced = sum(i["total_amount"] for i in invoices_out)
total_receipts = sum(r["amount"] for r in receipts)
open_ar = sum(i["total_amount"] for i in invoices_out if i["status"] in ("Open","Short Pay - Open"))
print(f"\n=== Summary ===")
print(f"Total Invoiced (Q1):  ${total_invoiced:>15,.2f}")
print(f"Total Cash Received:  ${total_receipts:>15,.2f}")
print(f"Open AR Balance:      ${open_ar:>15,.2f}")
print(f"\nScenarios embedded:")
print(f"  Missing GL postings:       {len(missing_gl)} invoices")
print(f"  Duplicate GL posting:      1 invoice ({dup_inv})")
print(f"  Short pays:                {len(short_pay_ids)} invoices")
print(f"  Written off (GL only):     {len(write_off_ids)} invoices")
print(f"  Unapplied cash:            {len(unapplied_cash_invoices)} receipts")
print(f"  Unapplied credit memos:    {len(unapplied_cm_ids)} memos")
print(f"  Timing differences:        {len(timing_diff_invoices)} receipts")
print("\nDone.")
