"""
Benchmark script — evaluates the combined extractor on 8 contracts.

Compares:
  - Monday best single model (RoBERTa or Gemini per field)
  - Today combined extractor (best model per field via FIELD_MODEL_MAP)

Run from the contract-extractor/ directory:
    python -m evaluate.benchmark
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from extractor.config import FIELD_MODEL_MAP, THRESHOLD_CORRECT, THRESHOLD_PARTIAL
from extractor.extraction import extract_contract

# ── 8 evaluation contracts ────────────────────────────────────────────
CONTRACTS = [
    {
        "name": "TechSolutions Service Agmt",
        "text": """SERVICE AGREEMENT
This Service Agreement is entered into as of March 1, 2022, between Meridian Financial Group, Inc.,
a Delaware corporation ("Client"), and TechSolutions LLC, a Texas limited liability company ("Provider").
TERM. This Agreement commences April 1, 2022 and expires March 31, 2024.
RENEWAL. Automatically renews for one-year terms unless either party provides ninety (90) days written notice.
GOVERNING LAW. Governed by laws of the State of Texas.
TERMINATION FOR CAUSE. Client may terminate immediately if Provider commits material fraud or fails to cure
a material breach within 15 days of written notice.
PAYMENT. Client shall pay $25,000 per quarter, due within 45 days of invoice.
PENALTIES. Late payments accrue interest at 2% per month.""",
        "gt": {
            "party_1": "Meridian Financial Group, Inc.", "party_2": "TechSolutions LLC",
            "effective_date": "March 1, 2022", "expiration_date": "March 31, 2024",
            "governing_law": "State of Texas",
            "renewal": "automatically renews for one-year terms unless either party provides ninety (90) days written notice",
            "termination_for_cause": "terminate immediately if Provider commits material fraud or fails to cure within 15 days",
            "payment_terms": "$25,000 per quarter due within 45 days",
            "penalties": "2% per month interest on late payments",
        }
    },
    {
        "name": "NovaPharma License Agmt",
        "text": """LICENSE AGREEMENT
Dated January 15, 2021, between NovaPharma Inc., a California corporation ("Licensor"),
and BioResearch Partners LP, a New York limited partnership ("Licensee").
EFFECTIVE DATE. Effective February 1, 2021. TERM. Continues until January 31, 2026.
RENEWAL. Automatically renews for successive two-year periods unless 120 days notice given.
GOVERNING LAW. Governed by laws of the State of California.
TERMINATION. Licensor may terminate if Licensee fails to pay within 30 days of written notice.
ROYALTIES. Licensee pays 8% of Net Sales quarterly.
PENALTIES. Failure to pay royalties results in liquidated damages of $100,000 per quarter.""",
        "gt": {
            "party_1": "NovaPharma Inc.", "party_2": "BioResearch Partners LP",
            "effective_date": "February 1, 2021", "expiration_date": "January 31, 2026",
            "governing_law": "State of California",
            "renewal": "automatically renews for successive two-year periods unless 120 days notice given",
            "termination_for_cause": "terminate if Licensee fails to pay within 30 days of written notice",
            "payment_terms": "8% of Net Sales quarterly",
            "penalties": "liquidated damages of $100,000 per quarter",
        }
    },
    {
        "name": "Acme Corp Distribution Agmt",
        "text": """DISTRIBUTION AGREEMENT
Entered July 1, 2020 between Acme Corporation, an Ohio corporation ("Supplier"),
and GlobalDist Ltd., a United Kingdom company ("Distributor").
TERM. In full force from July 1, 2020 and expires June 30, 2023.
RENEWAL. Either party may request renewal by providing written notice 60 days before expiration.
GOVERNING LAW. Governed by laws of the State of Ohio.
TERMINATION FOR CAUSE. Either party may terminate if the other becomes insolvent or fails to remedy
a breach within 45 days of written notice.
PAYMENT. Distributor pays within 30 days of invoice.
DAMAGES. Breach of exclusivity clause results in liquidated damages of $200,000 per occurrence.""",
        "gt": {
            "party_1": "Acme Corporation", "party_2": "GlobalDist Ltd.",
            "effective_date": "July 1, 2020", "expiration_date": "June 30, 2023",
            "governing_law": "State of Ohio",
            "renewal": "Either party may request renewal by providing written notice 60 days before expiration",
            "termination_for_cause": "terminate if the other becomes insolvent or fails to remedy breach within 45 days",
            "payment_terms": "Distributor pays within 30 days of invoice",
            "penalties": "liquidated damages of $200,000 per occurrence for breach of exclusivity",
        }
    },
    {
        "name": "Sterling Properties Lease",
        "text": """COMMERCIAL LEASE AGREEMENT
Entered September 15, 2022, between Sterling Properties LLC, a Florida LLC ("Landlord"),
and PrimeRetail Holdings Corp., a Georgia corporation ("Tenant").
LEASE TERM. Begins October 1, 2022 and ends September 30, 2027.
RENEWAL OPTION. Tenant has two options to renew for five years each, with 180 days notice.
GOVERNING LAW. Governed by laws of the State of Florida.
DEFAULT. Landlord may terminate upon 30 days written notice if Tenant fails to pay rent for two months.
RENT. Monthly rent $15,000 due on the first day of each month.
LATE FEE. Rent not received within 5 days incurs a late fee of $750 per day.""",
        "gt": {
            "party_1": "Sterling Properties LLC", "party_2": "PrimeRetail Holdings Corp.",
            "effective_date": "September 15, 2022", "expiration_date": "September 30, 2027",
            "governing_law": "State of Florida",
            "renewal": "two options to renew for five years each with 180 days notice",
            "termination_for_cause": "terminate upon 30 days written notice if Tenant fails to pay rent for two months",
            "payment_terms": "$15,000 monthly due on the first day of each month",
            "penalties": "$750 per day late fee",
        }
    },
    {
        "name": "Vertex Capital Tech Services",
        "text": """TECHNOLOGY SERVICES AGREEMENT
Entered May 1, 2024 between Vertex Capital Partners LLC, a Delaware LLC ("Client"),
and Zenith Digital Solutions Inc., a Massachusetts corporation ("Service Provider").
TERM. Effective May 1, 2024 through April 30, 2026.
RENEWAL. Automatically renews for one-year periods unless 60 days notice given.
GOVERNING LAW. Governed by laws of the Commonwealth of Massachusetts.
TERMINATION FOR CAUSE. Either party may terminate upon 30 days notice for material breach uncured within 30 days.
PAYMENT. Client pays $8,500 per month within 30 days of invoice.
PENALTIES. Data breach caused by Provider negligence results in liquidated damages of $75,000 per incident.""",
        "gt": {
            "party_1": "Vertex Capital Partners LLC", "party_2": "Zenith Digital Solutions Inc.",
            "effective_date": "May 1, 2024", "expiration_date": "April 30, 2026",
            "governing_law": "Commonwealth of Massachusetts",
            "renewal": "automatically renews for one-year periods unless 60 days notice given",
            "termination_for_cause": "terminate upon 30 days notice for material breach uncured within 30 days",
            "payment_terms": "$8,500 per month within 30 days of invoice",
            "penalties": "$75,000 liquidated damages per data breach incident",
        }
    },
    {
        "name": "AlphaGen Software License",
        "text": """SOFTWARE LICENSE AGREEMENT
Dated August 1, 2023, between AlphaGen Technologies Corp., a Washington corporation ("Licensor"),
and DataStream Analytics Inc., a Virginia corporation ("Licensee").
EFFECTIVE DATE. License effective September 1, 2023 through August 31, 2025.
RENEWAL. License renews automatically for one-year terms unless either party gives 90 days notice.
GOVERNING LAW. This Agreement shall be governed by the laws of the State of Washington.
TERMINATION. Licensor may terminate immediately upon written notice if Licensee breaches confidentiality.
LICENSE FEE. Licensee pays $50,000 annual license fee, due January 1 each year.
PENALTIES. Unauthorized use of software results in penalty of $500 per day per violation.""",
        "gt": {
            "party_1": "AlphaGen Technologies Corp.", "party_2": "DataStream Analytics Inc.",
            "effective_date": "September 1, 2023", "expiration_date": "August 31, 2025",
            "governing_law": "State of Washington",
            "renewal": "renews automatically for one-year terms unless either party gives 90 days notice",
            "termination_for_cause": "terminate immediately upon written notice if Licensee breaches confidentiality",
            "payment_terms": "$50,000 annual license fee due January 1 each year",
            "penalties": "$500 per day per violation for unauthorized use",
        }
    },
    {
        "name": "BlueSky NDA Agreement",
        "text": """NON-DISCLOSURE AGREEMENT
Entered June 10, 2023, between BlueSky Ventures Inc., a Nevada corporation ("Disclosing Party"),
and Quantum Research Group LLC, a Colorado LLC ("Receiving Party").
TERM. Effective June 10, 2023 and expires June 9, 2026.
RENEWAL. Agreement does not automatically renew. Parties must execute a new agreement.
GOVERNING LAW. Governed by the laws of the State of Nevada.
TERMINATION. Either party may terminate upon 30 days written notice.
COMPENSATION. No compensation is payable under this Agreement.
PENALTIES. Breach of confidentiality results in liquidated damages of $250,000 plus attorney fees.""",
        "gt": {
            "party_1": "BlueSky Ventures Inc.", "party_2": "Quantum Research Group LLC",
            "effective_date": "June 10, 2023", "expiration_date": "June 9, 2026",
            "governing_law": "State of Nevada",
            "renewal": "Agreement does not automatically renew. Parties must execute a new agreement",
            "termination_for_cause": "Either party may terminate upon 30 days written notice",
            "payment_terms": "No compensation payable",
            "penalties": "$250,000 liquidated damages plus attorney fees for breach",
        }
    },
    {
        "name": "PrimeCare Consulting Agmt",
        "text": """CONSULTING AGREEMENT
Dated February 15, 2022, between PrimeCare Health Systems Inc., an Illinois corporation ("Company"),
and MedTech Advisors LLC, a Michigan LLC ("Consultant").
TERM. Services commence March 1, 2022 and terminate February 28, 2023.
RENEWAL. Company may renew for additional one-year terms with 30 days written notice before expiration.
GOVERNING LAW. Governed by the laws of the State of Illinois.
TERMINATION FOR CAUSE. Company may terminate immediately if Consultant violates HIPAA or commits fraud.
FEES. Consultant receives $15,000 per month payable on the 15th of each month.
PENALTIES. Unauthorized disclosure of patient data results in $500,000 penalty per incident.""",
        "gt": {
            "party_1": "PrimeCare Health Systems Inc.", "party_2": "MedTech Advisors LLC",
            "effective_date": "February 15, 2022", "expiration_date": "February 28, 2023",
            "governing_law": "State of Illinois",
            "renewal": "Company may renew for additional one-year terms with 30 days written notice",
            "termination_for_cause": "terminate immediately if Consultant violates HIPAA or commits fraud",
            "payment_terms": "$15,000 per month payable on the 15th",
            "penalties": "$500,000 penalty per patient data disclosure incident",
        }
    },
]

FIELDS = [
    "party_1", "party_2", "effective_date", "expiration_date",
    "governing_law", "renewal", "termination_for_cause", "payment_terms", "penalties",
]

# Monday's best single model results (from benchmark)
MONDAY_ROBERTA = {
    "party_1": 0, "party_2": 0, "effective_date": 50, "expiration_date": 38,
    "governing_law": 75, "renewal": 75, "termination_for_cause": 0,
    "payment_terms": 0, "penalties": 0,
}
MONDAY_GEMINI = {
    "party_1": 88, "party_2": 100, "effective_date": 0, "expiration_date": 0,
    "governing_law": 0, "renewal": 25, "termination_for_cause": 38,
    "payment_terms": 75, "penalties": 38,
}


def token_f1(pred: str, gold: str) -> float:
    """
    Compute token-level F1 between predicted and gold answer.

    Standard metric used in SQuAD and CUAD evaluation.
    Measures word overlap rather than exact string match.
    """
    if not gold.strip():
        return 1.0 if "not found" in pred.lower() else 0.0
    if not pred.strip() or "not found" in pred.lower():
        return 0.0
    p = set(pred.lower().split())
    g = set(gold.lower().split())
    c = p & g
    if not c:
        return 0.0
    prec = len(c) / len(p)
    rec  = len(c) / len(g)
    return 2 * prec * rec / (prec + rec)


def badge(f1: float) -> str:
    """Convert F1 score to a display badge."""
    if f1 >= THRESHOLD_CORRECT: return "OK "
    if f1 >= THRESHOLD_PARTIAL: return "~~ "
    return "-- "


def run_benchmark():
    """Run the combined extractor on all 8 contracts and print comparison tables."""
    print("=" * 70)
    print("  COMBINED EXTRACTOR BENCHMARK — 8 CONTRACTS")
    print("=" * 70)
    print(f"  Field routing: {FIELD_MODEL_MAP}")
    print()

    results = []
    for idx, c in enumerate(CONTRACTS):
        print(f"  [{idx+1}/8] {c['name']}")
        t0 = time.perf_counter()
        profile = extract_contract(c["text"], contract_name=c["name"])
        elapsed = time.perf_counter() - t0

        row = {"name": c["name"][:35], "fields": {}}
        scores = []
        for field in FIELDS:
            val  = getattr(profile, field).value
            gold = c["gt"].get(field, "")
            f1   = token_f1(val, gold)
            scores.append(f1)
            row["fields"][field] = {
                "extracted":  val[:80],
                "gold":       gold[:80],
                "f1":         round(f1, 3),
                "badge":      badge(f1),
                "model_used": FIELD_MODEL_MAP[field],
            }
        row["mean_f1"] = round(sum(scores) / len(scores), 3)
        print(f"     mean F1={row['mean_f1']:.2f}  ({elapsed:.0f}s)")
        results.append(row)

    # Per-contract table
    W = 105
    SHORT = {
        "party_1":"P1","party_2":"P2","effective_date":"Eff",
        "expiration_date":"Exp","governing_law":"Law","renewal":"Ren",
        "termination_for_cause":"Term","payment_terms":"Pay","penalties":"Pen",
    }
    print(f"\n{'='*W}")
    print("  COMBINED EXTRACTOR — PER CONTRACT RESULTS")
    print(f"{'='*W}")
    hdr = f"{'Contract':<36}" + "".join(f"{SHORT[f]:>7}" for f in FIELDS) + "   Mean"
    print(hdr)
    print("-"*W)
    for row in results:
        line = f"{row['name']:<36}"
        for field in FIELDS:
            b = row["fields"][field]["badge"].strip()
            line += f"  [{b}]"
        line += f"   {row['mean_f1']:.2f}"
        print(line)
    print("-"*W)

    # Accuracy row
    combined_acc = {}
    acc_line = f"{'Combined Accuracy':<36}"
    for field in FIELDS:
        a = sum(1 for r in results if r["fields"][field]["f1"] >= THRESHOLD_CORRECT) / len(results) * 100
        combined_acc[field] = a
        acc_line += f"  {a:>3.0f}%"
    print(acc_line + f"   {sum(combined_acc.values())/len(combined_acc):.0f}%")
    print(f"{'='*W}")

    # Comparison table
    print(f"\n{'='*70}")
    print("  MONDAY vs TODAY — ACCURACY COMPARISON (same 8 contracts)")
    print(f"{'='*70}")
    print(f"  {'Field':<25} {'Mon RoBERTa':>12} {'Mon Gemini':>11} {'Combined':>10}  Change")
    print("  " + "-"*65)
    for field in FIELDS:
        rb  = MONDAY_ROBERTA[field]
        gem = MONDAY_GEMINI[field]
        mon_best = max(rb, gem)
        com = combined_acc[field]
        diff = com - mon_best
        change = f"+{diff:.0f}%" if diff > 0 else f"{diff:.0f}%"
        print(f"  {field:<25} {rb:>11}%  {gem:>10}%  {com:>9.0f}%  {change}")
    print("  " + "-"*65)
    rb_overall  = sum(MONDAY_ROBERTA.values()) / len(MONDAY_ROBERTA)
    gem_overall = sum(MONDAY_GEMINI.values())  / len(MONDAY_GEMINI)
    com_overall = sum(combined_acc.values())   / len(combined_acc)
    mon_best_overall = max(rb_overall, gem_overall)
    diff = com_overall - mon_best_overall
    change = f"+{diff:.0f}%" if diff > 0 else f"{diff:.0f}%"
    print(f"  {'Overall':<25} {rb_overall:>11.0f}%  {gem_overall:>10.0f}%  {com_overall:>9.0f}%  {change}")
    print(f"{'='*70}")

    # Save results
    out_path = Path(__file__).parent.parent / "sample_outputs" / "benchmark_results.json"
    with open(out_path, "w") as f:
        json.dump({"contracts": results, "accuracy": combined_acc}, f, indent=2)
    print(f"\nSaved -> {out_path}")


if __name__ == "__main__":
    run_benchmark()
