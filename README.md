# Contract Extractor

A hybrid NLP pipeline that extracts structured information from legal contracts using RoBERTa-base-CUAD (extractive QA) and Gemini 2.5 Flash (generative extraction). Each field is routed to the model that performs best for it.

Comes with both a **web UI** (drag and drop PDF → contract profile card) and a **Python package** (import and use in code).

---

## What It Does

Upload a PDF contract and get back a structured profile with nine fields extracted: party names, dates, governing law, renewal terms, payment terms, termination conditions, and penalties. The pipeline automatically uses the right model for each field — no model selection needed.

---

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher (for the UI only)
- A Gemini API key — free tier at [aistudio.google.com](https://aistudio.google.com)
- ~2 GB free RAM for the RoBERTa model
- Internet connection for first run (downloads ~500 MB model)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/BharatGoyal28/-contract-extractor.git
cd -contract-extractor

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Add your Gemini API key
# Create a .env file in the root folder:
GEMINI_API_KEY=your_key_here

# 4. Install frontend dependencies (for UI only)
cd frontend
npm install
cd ..
```

---

## Option A — Run With UI (Recommended)

**Terminal 1 — Backend:**
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8002
```

Wait for:
```
INFO:     Application startup complete.
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:5174** in your browser.

You will see:
- Drag and drop upload area
- Processing animation while extracting
- Contract profile card with all 9 fields
- Confidence bars and model badges per field
- Deadline flags for expiring contracts

---

## Option B — Use As Python Package

```python
from extractor import load_pdf, extract_contract, profile_to_dict

# From a PDF file
text    = load_pdf("your_contract.pdf")
profile = extract_contract(text, contract_name="your_contract.pdf")
result  = profile_to_dict(profile)

print(result["party_1"]["value"])        # Meridian Financial Group, Inc.
print(result["effective_date"]["value"]) # March 1, 2022
print(result["governing_law"]["value"])  # State of Texas
```

```python
# From raw text
from extractor import load_text, extract_contract, profile_to_dict

text    = load_text(open("contract.txt").read())
profile = extract_contract(text, contract_name="contract.txt")
result  = profile_to_dict(profile)
```

---

## How To Run The Benchmark

```bash
python -m evaluate.benchmark
```

Runs the combined extractor on 8 evaluation contracts and prints:
- Per-contract results table
- Accuracy comparison: single model vs combined extractor

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

Full sample: [`sample_outputs/example_output.json`](sample_outputs/example_output.json)

---

## Field Routing

Routing is fixed based on benchmark results. No user selection needed.

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
├── main.py                     # FastAPI server (port 8002)
├── .env                        # Add GEMINI_API_KEY here
├── extractor/
│   ├── __init__.py             # Public API
│   ├── config.py               # FIELD_MODEL_MAP and settings
│   ├── models.py               # RoBERTa and Gemini interfaces
│   ├── ingestion.py            # PDF loading and text cleaning
│   └── extraction.py           # Combined extraction pipeline
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main app — no model dropdown
│   │   └── components/
│   │       ├── UploadZone.jsx
│   │       ├── ProcessingState.jsx
│   │       └── ContractProfile.jsx
│   └── vite.config.js          # Runs on port 5174
├── evaluate/
│   ├── benchmark.py            # 8-contract evaluation script
│   └── build_comparison.py     # Comparison table from saved data
└── sample_outputs/
    └── example_output.json     # Sample pipeline output
```

---

## Notes

- First run downloads RoBERTa model (~500 MB) — takes ~2 minutes
- Subsequent runs load from cache in ~8 seconds
- Gemini free tier: 20 requests/day — each contract uses 5 Gemini calls
- Rate limit handling: exponential backoff built in automatically
- UI runs on port **5174**, backend on port **8002**
