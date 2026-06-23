"""
FastAPI server for the Contract Extractor.
Routing is fixed — no model selection needed.
All fields use FIELD_MODEL_MAP from extractor/config.py.

Run: python -m uvicorn main:app --host 127.0.0.1 --port 8002
"""

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv(Path(__file__).parent / ".env")

from extractor.ingestion import load_pdf, load_text
from extractor.extraction import extract_contract, profile_to_dict

app = FastAPI(title="Contract Extractor", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Liveness check."""
    key = os.environ.get("GEMINI_API_KEY", "")
    return {
        "status": "ok",
        "gemini_key_set": bool(key) and "your_gemini" not in key,
    }


@app.post("/extract")
async def extract_from_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF contract and extract all 9 fields.
    Model routing is fixed via FIELD_MODEL_MAP in extractor/config.py.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = load_pdf(tmp_path)
        if not text.strip():
            raise HTTPException(422, "Could not extract text from PDF.")
        profile = extract_contract(text, contract_name=file.filename)
        return JSONResponse(profile_to_dict(profile))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
