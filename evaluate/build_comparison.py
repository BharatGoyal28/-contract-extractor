"""
Builds the Monday vs Combined comparison table from saved data.
No model loading. No API calls. Uses cached results only.
Run: python -m evaluate.build_comparison
"""

from pathlib import Path
import json

OUTPUT_DIR = Path(__file__).parent.parent.parent / "legal-ai" / "backend" / "evaluation_results"

FIELDS = [
    "party_1", "party_2", "effective_date", "expiration_date",
    "governing_law", "renewal", "termination_for_cause",
    "payment_terms", "penalties",
]

SHORT = {
    "party_1":"P1","party_2":"P2","effective_date":"Eff",
    "expiration_date":"Exp","governing_law":"Law","renewal":"Ren",
    "termination_for_cause":"Term","payment_terms":"Pay","penalties":"Pen",
}

# ── Monday results (8 contracts, from benchmark) ──────────────────────
MONDAY_ROBERTA = {
    "party_1":0,"party_2":0,"effective_date":50,"expiration_date":38,
    "governing_law":75,"renewal":75,"termination_for_cause":0,
    "payment_terms":0,"penalties":0,
}

MONDAY_GEMINI = {
    "party_1":88,"party_2":100,"effective_date":0,"expiration_date":0,
    "governing_law":0,"renewal":25,"termination_for_cause":38,
    "payment_terms":75,"penalties":38,
}

# ── FIELD_MODEL_MAP (from config.py) ─────────────────────────────────
FIELD_MODEL_MAP = {
    "party_1":               "gemini",
    "party_2":               "gemini",
    "effective_date":        "roberta",
    "expiration_date":       "roberta",
    "governing_law":         "roberta",
    "renewal":               "roberta",
    "termination_for_cause": "gemini",
    "payment_terms":         "gemini",
    "penalties":             "gemini",
}

# ── Per contract results (8 contracts, from saved data) ───────────────
# RoBERTa scores from evaluate_15 run
# Gemini scores from compare_3 + gemini_remaining runs

CONTRACTS = [
    {
        "name": "TechSolutions Service Agmt",
        "roberta": {"party_1":0.00,"party_2":0.00,"effective_date":1.00,"expiration_date":1.00,"governing_law":0.40,"renewal":0.93,"termination_for_cause":0.00,"payment_terms":0.00,"penalties":0.00},
        "gemini":  {"party_1":1.00,"party_2":1.00,"effective_date":0.00,"expiration_date":0.00,"governing_law":0.00,"renewal":0.54,"termination_for_cause":0.19,"payment_terms":0.33,"penalties":0.62},
    },
    {
        "name": "NovaPharma License Agmt",
        "roberta": {"party_1":0.00,"party_2":0.00,"effective_date":0.00,"expiration_date":0.00,"governing_law":1.00,"renewal":0.91,"termination_for_cause":0.00,"payment_terms":0.00,"penalties":0.00},
        "gemini":  {"party_1":0.29,"party_2":1.00,"effective_date":0.00,"expiration_date":0.00,"governing_law":0.00,"renewal":0.70,"termination_for_cause":0.60,"payment_terms":0.73,"penalties":0.56},
    },
    {
        "name": "Acme Corp Distribution Agmt",
        "roberta": {"party_1":0.00,"party_2":0.00,"effective_date":0.00,"expiration_date":0.00,"governing_law":0.40,"renewal":0.85,"termination_for_cause":0.00,"payment_terms":0.00,"penalties":0.50},
        "gemini":  {"party_1":1.00,"party_2":1.00,"effective_date":0.00,"expiration_date":0.00,"governing_law":0.00,"renewal":0.80,"termination_for_cause":0.65,"payment_terms":0.70,"penalties":0.60},
    },
    {
        "name": "Sterling Properties Lease",
        "roberta": {"party_1":0.00,"party_2":0.00,"effective_date":0.35,"expiration_date":0.00,"governing_law":1.00,"renewal":0.67,"termination_for_cause":0.00,"payment_terms":0.00,"penalties":0.00},
        "gemini":  {"party_1":1.00,"party_2":1.00,"effective_date":0.00,"expiration_date":0.00,"governing_law":0.00,"renewal":0.45,"termination_for_cause":0.70,"payment_terms":0.75,"penalties":0.35},
    },
    {
        "name": "Vertex Capital Tech Services",
        "roberta": {"party_1":0.00,"party_2":0.00,"effective_date":1.00,"expiration_date":0.00,"governing_law":1.00,"renewal":0.90,"termination_for_cause":0.00,"payment_terms":0.00,"penalties":0.57},
        "gemini":  {"party_1":1.00,"party_2":1.00,"effective_date":0.00,"expiration_date":0.00,"governing_law":0.00,"renewal":0.67,"termination_for_cause":0.12,"payment_terms":0.75,"penalties":0.00},
    },
    {
        "name": "AlphaGen Software License",
        "roberta": {"party_1":0.00,"party_2":0.00,"effective_date":1.00,"expiration_date":1.00,"governing_law":1.00,"renewal":1.00,"termination_for_cause":0.00,"payment_terms":0.00,"penalties":0.00},
        "gemini":  {"party_1":1.00,"party_2":1.00,"effective_date":0.00,"expiration_date":0.00,"governing_law":0.00,"renewal":0.60,"termination_for_cause":0.75,"payment_terms":0.80,"penalties":0.70},
    },
    {
        "name": "BlueSky NDA Agreement",
        "roberta": {"party_1":0.00,"party_2":0.00,"effective_date":1.00,"expiration_date":1.00,"governing_law":1.00,"renewal":0.00,"termination_for_cause":0.00,"payment_terms":0.00,"penalties":0.00},
        "gemini":  {"party_1":1.00,"party_2":1.00,"effective_date":0.00,"expiration_date":0.00,"governing_law":0.00,"renewal":0.00,"termination_for_cause":0.55,"payment_terms":0.00,"penalties":0.80},
    },
    {
        "name": "PrimeCare Consulting Agmt",
        "roberta": {"party_1":0.00,"party_2":0.00,"effective_date":0.35,"expiration_date":0.00,"governing_law":1.00,"renewal":1.00,"termination_for_cause":0.00,"payment_terms":0.00,"penalties":0.00},
        "gemini":  {"party_1":1.00,"party_2":1.00,"effective_date":0.00,"expiration_date":0.00,"governing_law":0.00,"renewal":0.50,"termination_for_cause":0.75,"payment_terms":0.80,"penalties":0.70},
    },
]

def badge(f1):
    if f1 >= 0.7: return "OK "
    if f1 >= 0.3: return "~~ "
    return "-- "

def combined_f1(contract, field):
    """Pick the score from whichever model FIELD_MODEL_MAP assigns to this field."""
    model = FIELD_MODEL_MAP[field]
    return contract[model][field]

# ── Per contract combined table ───────────────────────────────────────
W = 105
cols = [SHORT[f] for f in FIELDS]

print(f"\n{'='*W}")
print("  COMBINED EXTRACTOR — PER CONTRACT RESULTS (8 contracts)")
print("  RoBERTa for: EffDate, ExpDate, Law, Renewal")
print("  Gemini for:  Party1, Party2, Term, Payment, Penalty")
print(f"{'='*W}")
hdr = f"{'Contract':<36}" + "".join(f"{c:>7}" for c in cols) + "   Mean"
print(hdr)
print("-"*W)

combined_acc = {f: [] for f in FIELDS}

for c in CONTRACTS:
    line = f"{c['name']:<36}"
    scores = []
    for field in FIELDS:
        f1 = combined_f1(c, field)
        combined_acc[field].append(f1)
        scores.append(f1)
        b = badge(f1).strip()
        line += f"  [{b}]"
    mean = sum(scores)/len(scores)
    line += f"   {mean:.2f}"
    print(line)

print("-"*W)

# Accuracy row
acc_line = f"{'Accuracy':<36}"
field_acc = {}
for field in FIELDS:
    a = sum(1 for s in combined_acc[field] if s >= 0.7) / 8 * 100
    field_acc[field] = a
    acc_line += f"  {a:>3.0f}%"
overall = sum(field_acc.values())/len(field_acc)
print(acc_line + f"   {overall:.0f}%")
print(f"{'='*W}")

# ── Monday vs Combined comparison ─────────────────────────────────────
print(f"\n{'='*70}")
print("  MONDAY vs TODAY — ACCURACY COMPARISON (same 8 contracts)")
print(f"{'='*70}")
print(f"  {'Field':<25} {'Mon RoBERTa':>12} {'Mon Gemini':>11} {'Combined':>10}  Change")
print("  " + "-"*62)

for field in FIELDS:
    rb  = MONDAY_ROBERTA[field]
    gem = MONDAY_GEMINI[field]
    mon_best = max(rb, gem)
    com = field_acc[field]
    diff = com - mon_best
    change = f"+{diff:.0f}%" if diff > 0 else f"{diff:.0f}%"
    model_used = FIELD_MODEL_MAP[field].upper()
    print(f"  {field:<25} {rb:>11}%  {gem:>10}%  {com:>9.0f}%  {change}  [{model_used}]")

print("  " + "-"*62)
rb_o  = sum(MONDAY_ROBERTA.values())/len(MONDAY_ROBERTA)
gem_o = sum(MONDAY_GEMINI.values())/len(MONDAY_GEMINI)
com_o = sum(field_acc.values())/len(field_acc)
diff  = com_o - max(rb_o, gem_o)
change = f"+{diff:.0f}%" if diff > 0 else f"{diff:.0f}%"
print(f"  {'Overall':<25} {rb_o:>11.0f}%  {gem_o:>10.0f}%  {com_o:>9.0f}%  {change}")
print(f"{'='*70}")

# Save
out = {
    "field_accuracy": field_acc,
    "overall": com_o,
    "monday_roberta": MONDAY_ROBERTA,
    "monday_gemini": MONDAY_GEMINI,
}
out_path = Path(__file__).parent.parent / "sample_outputs" / "comparison_table.json"
with open(out_path, "w") as f:
    json.dump(out, f, indent=2)
print(f"\nSaved -> {out_path}")
print("Done.")
