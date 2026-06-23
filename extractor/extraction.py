"""
Combined field extraction pipeline.

Routes each field to the correct model based on FIELD_MODEL_MAP in config.py.
Applies post-processing to clean RoBERTa's verbose span output.

The routing is explicit — FIELD_MODEL_MAP is the single source of truth.
Changing which model handles a field requires only editing config.py.
"""

import re
import time
from dataclasses import asdict, dataclass

from extractor.config import FIELD_MODEL_MAP, THRESHOLD_CORRECT, THRESHOLD_PARTIAL
from extractor.models import roberta_extract, gemini_extract


# ── Post-processing patterns ──────────────────────────────────────────

_DATE_RE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},?\s+\d{4}\b"
    r"|\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b",
    re.IGNORECASE,
)

_STATE_RE = re.compile(
    r"(?:State|Commonwealth|Province)\s+of\s+[\w\s]+?(?=,|\.|$|\s+without|\s+law)",
    re.IGNORECASE,
)

_PARTY_RE = re.compile(
    r"([A-Z][A-Za-z0-9\s\.\,\-&']+?"
    r"(?:Inc\.|LLC|Ltd\.|Corp\.|Corporation|Limited|L\.P\.|LLP|LP|Company|Co\.))",
    re.IGNORECASE,
)

_BOILERPLATE = re.compile(
    r"^(?:this agreement|the agreement|this contract|the contract|"
    r"this lease|this license|pursuant to|subject to|in accordance with)\s+",
    re.IGNORECASE,
)


def _clean_date(raw: str, prefer_last: bool = False) -> str:
    """Extract a clean date string from a verbose RoBERTa span."""
    if not raw or "not found" in raw.lower():
        return raw
    if len(raw) <= 40:
        return raw
    matches = _DATE_RE.findall(raw)
    if not matches:
        return raw[:80]
    return matches[-1] if prefer_last else matches[0]


def _clean_governing_law(raw: str) -> str:
    """Extract just the state/country name from a RoBERTa governing law span."""
    if not raw or "not found" in raw.lower():
        return raw
    if len(raw) <= 40:
        return raw
    m = _STATE_RE.search(raw)
    return m.group(0).strip() if m else raw[:80]


def _clean_party(raw: str) -> str:
    """Extract a clean company name from a RoBERTa party span."""
    if not raw or "not found" in raw.lower():
        return raw
    if len(raw) <= 60:
        return raw.strip()
    matches = _PARTY_RE.findall(raw)
    if matches:
        return matches[0].strip().rstrip(",")
    cleaned = _BOILERPLATE.sub("", raw).strip()
    for sep in [" (", ", a ", ", an "]:
        if sep in cleaned:
            return cleaned[:cleaned.index(sep)].strip()
    return cleaned[:80]


def _postprocess(field: str, raw: str) -> str:
    """
    Apply field-specific post-processing to clean RoBERTa output.

    RoBERTa returns full sentences — these rules strip them to core values.
    Gemini output is generally clean and does not need post-processing.
    """
    if not raw or "not found" in raw.lower():
        return raw
    if field == "effective_date":
        return _clean_date(raw, prefer_last=False)
    if field == "expiration_date":
        return _clean_date(raw, prefer_last=True)
    if field == "governing_law":
        return _clean_governing_law(raw)
    if field in ("party_1", "party_2"):
        return _clean_party(raw)
    # For clause fields, just trim to 160 chars
    return raw[:160] + ("…" if len(raw) > 160 else "")


# ── Result dataclass ──────────────────────────────────────────────────

@dataclass
class FieldResult:
    """Extraction result for a single field."""
    value: str
    confidence: float    # 0-1, RoBERTa gives a real score; Gemini uses 0.85 default
    source: str          # "roberta" or "gemini"
    latency_ms: int
    model_used: str      # explicit — matches FIELD_MODEL_MAP value


@dataclass
class ContractProfile:
    """Full extraction result for one contract."""
    contract_name: str
    party_1: FieldResult
    party_2: FieldResult
    effective_date: FieldResult
    expiration_date: FieldResult
    renewal: FieldResult
    governing_law: FieldResult
    termination_for_cause: FieldResult
    payment_terms: FieldResult
    penalties: FieldResult
    total_latency_ms: int


# ── Main extraction function ──────────────────────────────────────────

def extract_contract(contract_text: str, contract_name: str = "") -> ContractProfile:
    """
    Extract all 9 fields from a contract using the configured model per field.

    Routing is determined by FIELD_MODEL_MAP in config.py.
    Each field is extracted independently and results are assembled
    into a ContractProfile.

    Args:
        contract_text: full text of the contract
        contract_name: optional name for logging

    Returns:
        ContractProfile with all 9 fields extracted
    """
    t_start = time.perf_counter()
    results = {}

    for field, model in FIELD_MODEL_MAP.items():
        if model == "roberta":
            rb = roberta_extract(field, contract_text)
            cleaned = _postprocess(field, rb.answer)
            results[field] = FieldResult(
                value=cleaned,
                confidence=rb.score,
                source="roberta",
                latency_ms=rb.latency_ms,
                model_used="roberta",
            )
        else:
            gem = gemini_extract(field, contract_text)
            ans = gem.answer
            conf = 0.85 if "not found" not in ans.lower() and "error" not in ans.lower() else 0.0
            results[field] = FieldResult(
                value=ans,
                confidence=conf,
                source="gemini",
                latency_ms=gem.latency_ms,
                model_used="gemini",
            )

    total_ms = int((time.perf_counter() - t_start) * 1000)

    return ContractProfile(
        contract_name=contract_name,
        party_1=results["party_1"],
        party_2=results["party_2"],
        effective_date=results["effective_date"],
        expiration_date=results["expiration_date"],
        renewal=results["renewal"],
        governing_law=results["governing_law"],
        termination_for_cause=results["termination_for_cause"],
        payment_terms=results["payment_terms"],
        penalties=results["penalties"],
        total_latency_ms=total_ms,
    )


def profile_to_dict(profile: ContractProfile) -> dict:
    """Convert a ContractProfile to a JSON-serialisable dictionary."""
    return asdict(profile)
