"""
PDF and text ingestion for the contract extraction pipeline.

Handles loading contract text from PDF files or raw strings,
and applies basic cleaning before passing to the extractors.
"""

import re
from pathlib import Path

import pdfplumber


def load_pdf(path: str | Path) -> str:
    """
    Extract all text from a PDF file.

    Reads each page using pdfplumber and joins the text.
    Collapses multiple blank lines to a single blank line.

    Args:
        path: path to the PDF file

    Returns:
        Cleaned contract text as a single string
    """
    text_parts = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)

    raw = "\n".join(text_parts)
    return _clean(raw)


def load_text(text: str) -> str:
    """
    Clean raw contract text passed as a string.

    Args:
        text: raw contract text

    Returns:
        Cleaned contract text
    """
    return _clean(text)


def _clean(text: str) -> str:
    """
    Normalise whitespace in contract text.

    Collapses 3+ consecutive newlines to 2,
    strips leading/trailing whitespace.
    """
    cleaned = re.sub(r"\n{3,}", "\n\n", text)
    return cleaned.strip()
