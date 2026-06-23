"""
Central configuration for the contract extraction pipeline.

FIELD_MODEL_MAP tells the pipeline which model to use for each field.
This is the single place to change routing decisions — no logic buried elsewhere.

Routing decisions based on Monday benchmark (8 contracts):
- Gemini wins on: party names, payment terms, termination, penalties
- RoBERTa wins on: dates, governing law, renewal
"""

# ── Field to model routing ────────────────────────────────────────────
# Change values here to switch which model handles which field.
# Valid values: "gemini" or "roberta"

FIELD_MODEL_MAP = {
    "party_1":               "gemini",    # Gemini 88%  vs RoBERTa  0%
    "party_2":               "gemini",    # Gemini 100% vs RoBERTa  0%
    "effective_date":        "roberta",   # RoBERTa 50% vs Gemini   0%
    "expiration_date":       "roberta",   # RoBERTa 38% vs Gemini   0%
    "governing_law":         "roberta",   # RoBERTa 75% vs Gemini   0%
    "renewal":               "roberta",   # RoBERTa 75% vs Gemini  25%
    "termination_for_cause": "gemini",    # Gemini  38% vs RoBERTa  0%
    "payment_terms":         "gemini",    # Gemini  75% vs RoBERTa  0%
    "penalties":             "gemini",    # Gemini  38% vs RoBERTa  0%
}

# ── Model settings ────────────────────────────────────────────────────
ROBERTA_MODEL_ID  = "akdeniz27/roberta-base-cuad"
GEMINI_MODEL_ID   = "gemini-2.5-flash"

# RoBERTa chunking
ROBERTA_MAX_LEN   = 512   # tokens per chunk
ROBERTA_STRIDE    = 128   # overlap between chunks

# Gemini text limit (characters sent per prompt)
GEMINI_MAX_CHARS  = 50000

# Gemini rate limiting
GEMINI_MIN_GAP_S  = 6.0   # minimum seconds between calls
GEMINI_MAX_RETRIES = 8    # max retry attempts on rate limit

# Accuracy thresholds for result labelling
THRESHOLD_CORRECT = 0.7   # F1 >= 0.7 = correct
THRESHOLD_PARTIAL = 0.3   # F1 >= 0.3 = partial match
