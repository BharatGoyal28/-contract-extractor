"""
Contract Extractor — combined RoBERTa + Gemini pipeline.

Main entry point:
    from extractor.extraction import extract_contract
    profile = extract_contract(contract_text, contract_name="my_contract.pdf")
"""

from extractor.extraction import extract_contract, profile_to_dict
from extractor.ingestion import load_pdf, load_text

__all__ = ["extract_contract", "profile_to_dict", "load_pdf", "load_text"]
