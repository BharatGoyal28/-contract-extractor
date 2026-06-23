# Contract Extractor

A hybrid NLP pipeline that extracts structured information from legal contracts using RoBERTa-base-CUAD (extractive QA) and Gemini 2.5 Flash (generative extraction). Each field is routed to the model that performs best for it.

---

## What It Does

Upload a PDF contract and get back a structured JSON with nine fields extracted: party names, dates, governing law, renewal terms, payment terms, termination conditions, and penalties. The pipeline automatically uses the right model for each field based on benchmark results.

---

## Prerequisites

- Python 3.10 or higher
- A Gemini API key (free tier available at [aistudio.google.com](https://aistudio.google.com))
- ~2 GB free RAM for the RoBERTa model
- Internet connection for first run (downloads ~500 MB model)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/contract-extractor.git
cd contract-extractor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env
```

---

## How To Run On A Single Contract

**From a PDF file:**
```python
from extractor import load_pdf, extract_contract, profile_to_dict

text    = load_pdf("your_contract.pdf")
profile = extract_contract(text, contract_name="your_contract.pdf")
result  = profile_to_dict(profile)

print(result["party_1"]["value"])       # Acme Corporation
print(result["effective_date"]["value"]) # January 1, 2023
```

**From raw text:**
```python
from extractor import load_text, extract_contract, profile_to_dict

text    = load_text(open("contract.txt").read())
profile = extract_contract(text, contract_name="contract.txt")
result  = profile_to_dict(profile)
```

---

## How To Run The Benchmark

```bash
cd contract-extractor
python -m evaluate.benchmark
```

Runs the combined extractor on 8 evaluation contracts and prints:
- Per-contract results table
- Accuracy comparison: Monday single model vs combined extractor

---

## What The Output Looks Like

```json
{
  "contract_name": "TechSolutions_ServiceAgreement.pdf",
  "party_1": {
    "value": "Meridian Financial Group, Inc.",
    "confidence": 0.85,
    "source": "gemini",
    "model_used": "gemini",
    "latency_ms": 3241
  },
  "effective_date": {
    "value": "March 1, 2022",
    "confidence": 0.78,
    "source": "roberta",
    "model_used": "roberta",
    "latency_ms": 1423
  },
  "governing_law": {
    "value": "State of Texas",
    "confidence": 0.86,
    "source": "roberta",
    "model_used": "roberta",
    "latency_ms": 1267
  },
  "total_latency_ms": 19372
}
```

Full sample output: [`sample_outputs/example_output.json`](sample_outputs/example_output.json)

---

## Field Routing

Each field is routed to the model that performed best in benchmarking:

| Field | Model | Accuracy |
|-------|-------|----------|
| party_1 | Gemini | 88% |
| party_2 | Gemini | 100% |
| effective_date | RoBERTa | 50% |
| expiration_date | RoBERTa | 38% |
| governing_law | RoBERTa | 75% |
| renewal | RoBERTa | 75% |
| termination_for_cause | Gemini | 38% |
| payment_terms | Gemini | 75% |
| penalties | Gemini | 38% |

To change routing, edit `FIELD_MODEL_MAP` in [`extractor/config.py`](extractor/config.py).

---

## Project Structure

```
contract-extractor/
├── README.md
├── requirements.txt
├── .env                        # Add your GEMINI_API_KEY here
├── extractor/
│   ├── __init__.py             # Public API
│   ├── config.py               # FIELD_MODEL_MAP and settings
│   ├── models.py               # RoBERTa and Gemini interfaces
│   ├── ingestion.py            # PDF loading and text cleaning
│   └── extraction.py           # Combined extraction pipeline
├── evaluate/
│   └── benchmark.py            # Evaluation script
└── sample_outputs/
    └── example_output.json     # Sample pipeline output
```

---

## Notes

- First run downloads the RoBERTa model (~500 MB) and takes ~2 minutes
- Subsequent runs load from cache in ~8 seconds
- Gemini free tier: 20 requests/day. Each contract uses 5 calls (one per Gemini field)
- Rate limit handling: automatic exponential backoff built in
