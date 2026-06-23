"""
Model interfaces for RoBERTa-base-CUAD and Gemini 2.5 Flash.

RoBERTa: extractive QA — finds the exact span in the contract text.
Gemini:  generative extraction — reads and produces a summary answer.
"""

import math
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import torch
from transformers import AutoModelForQuestionAnswering, AutoTokenizer
from google import genai
from google.genai import types as gtypes

from extractor.config import (
    ROBERTA_MODEL_ID, ROBERTA_MAX_LEN, ROBERTA_STRIDE,
    GEMINI_MODEL_ID, GEMINI_MAX_CHARS,
    GEMINI_MIN_GAP_S, GEMINI_MAX_RETRIES,
)

# ── CUAD questions for RoBERTa ────────────────────────────────────────
# Specific questions for each field — short and direct for better span precision.

CUAD_QUESTIONS = {
    "effective_date":        "What is the exact effective date or signing date of this contract?",
    "expiration_date":       "What is the exact expiration date or end date of this contract?",
    "governing_law":         "Which state or country law governs this contract?",
    "renewal":               "What are the renewal terms of this contract?",
    "termination_for_cause": "What are the conditions under which a party may terminate this contract for cause?",
    "penalties":             "What are the penalties or liquidated damages for breach of this contract?",
    "party_1":               "What is the full legal name of the first party in this contract?",
    "party_2":               "What is the full legal name of the second party in this contract?",
    "payment_terms":         "What are the payment terms and amounts in this contract?",
}

# ── Gemini prompts ────────────────────────────────────────────────────
GEMINI_PROMPTS = {
    "party_1": (
        "From this contract extract the full legal name of the FIRST party "
        "(Client, Licensor, Buyer, or similar). Return ONLY the name.\n\nCONTRACT:\n{text}"
    ),
    "party_2": (
        "From this contract extract the full legal name of the SECOND party "
        "(Provider, Licensee, Seller, or similar). Return ONLY the name.\n\nCONTRACT:\n{text}"
    ),
    "termination_for_cause": (
        "From this contract extract the termination for cause clause — "
        "what constitutes cause, notice period, cure period. One sentence. "
        "If none: 'Not found in contract'.\n\nCONTRACT:\n{text}"
    ),
    "payment_terms": (
        "From this contract extract the payment terms and amounts. One sentence. "
        "If none: 'Not found in contract'.\n\nCONTRACT:\n{text}"
    ),
    "penalties": (
        "From this contract extract penalty or liquidated damages clauses. One sentence. "
        "If none: 'Not found in contract'.\n\nCONTRACT:\n{text}"
    ),
}


# ── RoBERTa ───────────────────────────────────────────────────────────

_rb_tokenizer = None
_rb_model = None


def _load_roberta():
    """Load RoBERTa model and tokenizer from HuggingFace (cached after first run)."""
    global _rb_tokenizer, _rb_model
    if _rb_tokenizer is None:
        print(f"[RoBERTa] Loading {ROBERTA_MODEL_ID}...")
        _rb_tokenizer = AutoTokenizer.from_pretrained(ROBERTA_MODEL_ID)
        _rb_model = AutoModelForQuestionAnswering.from_pretrained(ROBERTA_MODEL_ID)
        _rb_model.eval()
        print("[RoBERTa] Ready.")
    return _rb_tokenizer, _rb_model


@dataclass
class RoBERTaResult:
    """Result from RoBERTa extractive QA."""
    answer: str
    score: float      # normalised confidence 0-1
    latency_ms: int


def roberta_extract(field: str, contract_text: str) -> RoBERTaResult:
    """
    Run extractive QA for one field using RoBERTa-base-CUAD.

    Uses a sliding window to handle contracts longer than 512 tokens.
    Picks the span with the highest combined start+end logit across all chunks.

    Args:
        field: one of the keys in CUAD_QUESTIONS
        contract_text: full contract text

    Returns:
        RoBERTaResult with answer span, confidence score, and latency
    """
    if field not in CUAD_QUESTIONS:
        return RoBERTaResult("Not found in contract", 0.0, 0)

    tok, mdl = _load_roberta()
    question = CUAD_QUESTIONS[field]
    t0 = time.perf_counter()

    enc = tok(
        question,
        contract_text[:50000],
        return_tensors="pt",
        truncation="only_second",
        max_length=ROBERTA_MAX_LEN,
        stride=ROBERTA_STRIDE,
        return_overflowing_tokens=True,
        padding="max_length",
    )

    best_text = ""
    best_score = -1e9

    for i in range(enc["input_ids"].shape[0]):
        chunk = {k: v[i].unsqueeze(0) for k, v in enc.items() if k != "overflow_to_sample_mapping"}

        with torch.no_grad():
            out = mdl(**chunk)

        sl, el = out.start_logits[0], out.end_logits[0]
        seq_ids = enc.sequence_ids(i)

        # Mask question tokens — only search within contract context
        ctx_s = next((j for j, s in enumerate(seq_ids) if s == 1), 0)
        ctx_e = next((len(seq_ids)-1-j for j, s in enumerate(reversed(seq_ids)) if s == 1), len(seq_ids)-1)

        mask = torch.full_like(sl, -1e9)
        mask[ctx_s:ctx_e+1] = 0
        sl, el = sl+mask, el+mask

        si = int(sl.argmax())
        # Limit answer window to 30 tokens — longer spans are almost always wrong
        window_end = min(si+30, ctx_e)
        ec = el[si:window_end+1]
        if not ec.numel():
            continue

        ei = si + int(ec.argmax())
        score = float(sl[si]) + float(el[ei])

        if score > best_score:
            best_score = score
            best_text = tok.decode(enc["input_ids"][i][si:ei+1], skip_special_tokens=True).strip()

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    norm_score = 1 / (1 + math.exp(-best_score / 10)) if best_score > -1e8 else 0.0

    if not best_text:
        return RoBERTaResult("Not found in contract", 0.0, elapsed_ms)
    return RoBERTaResult(best_text, round(norm_score, 3), elapsed_ms)


# ── Gemini ────────────────────────────────────────────────────────────

_gemini_client = None
_gemini_lock = threading.Lock()
_last_gemini_call: float = 0.0


def _get_gemini_client():
    """Initialise Gemini client using GEMINI_API_KEY from environment."""
    global _gemini_client
    if _gemini_client is None:
        key = os.environ.get("GEMINI_API_KEY", "")
        if not key or "your_gemini" in key:
            raise RuntimeError("GEMINI_API_KEY not set in .env")
        _gemini_client = genai.Client(api_key=key)
    return _gemini_client


@dataclass
class GeminiResult:
    """Result from Gemini generative extraction."""
    answer: str
    latency_ms: int
    cached: bool = False


def gemini_extract(field: str, contract_text: str) -> GeminiResult:
    """
    Run generative extraction for one field using Gemini 2.5 Flash.

    Includes exponential backoff on rate limit errors and a minimum
    inter-call gap to stay within free tier limits (10 RPM).

    Args:
        field: one of the keys in GEMINI_PROMPTS
        contract_text: full contract text

    Returns:
        GeminiResult with answer text and latency
    """
    global _last_gemini_call

    if field not in GEMINI_PROMPTS:
        return GeminiResult("Not found in contract", 0)

    prompt = GEMINI_PROMPTS[field].format(text=contract_text[:GEMINI_MAX_CHARS])

    with _gemini_lock:
        # Enforce minimum gap between calls
        wait = GEMINI_MIN_GAP_S - (time.time() - _last_gemini_call)
        if wait > 0:
            time.sleep(wait)

        client = _get_gemini_client()
        delay = 2.0
        answer = "Not found in contract"
        t0 = time.perf_counter()

        for attempt in range(GEMINI_MAX_RETRIES):
            try:
                resp = client.models.generate_content(
                    model=GEMINI_MODEL_ID,
                    contents=prompt,
                    config=gtypes.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=200,
                    ),
                )
                _last_gemini_call = time.time()
                answer = resp.text.strip() if resp.text else "Not found in contract"
                break
            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                    print(f"  [Gemini] Rate limit attempt {attempt+1}, sleeping {delay:.0f}s")
                    time.sleep(delay)
                    delay = min(delay * 2, 60)
                    _last_gemini_call = time.time()
                elif "503" in err:
                    time.sleep(5)
                else:
                    answer = f"Error: {err[:80]}"
                    break
        else:
            answer = "Not found in contract (rate limit exhausted)"

        latency_ms = int((time.perf_counter() - t0) * 1000)

    return GeminiResult(answer, latency_ms)
