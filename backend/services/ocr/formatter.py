"""
formatter.py
-------------
Top-level formatting router for the AI Medical Report Simplifier.

Pipeline:

    raw OCR text
        |
        v
    clean_text()              (formatters.generic_formatter)
        |
        v
    detect_document_type()    (formatters.detector)
        |
        v
    dispatch to:
        - format_lab_report()          (lab)
        - format_prescription()        (prescription)
        - format_pharmacy_bill()       (pharmacy)
        - format_generic()             (fallback)
        |
        v
    formatted string

This module does not implement any extraction logic itself — it only
orchestrates the specialized formatters in `formatters/`.
"""

import logging

from formatters import (
    clean_text,
    detect_document_type,
    format_generic,
    format_lab_report,
    format_pharmacy_bill,
    format_prescription,
)

logger = logging.getLogger(__name__)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


# Maps a detected document type to its corresponding formatter function.
_FORMATTER_DISPATCH = {
    "lab": format_lab_report,
    "prescription": format_prescription,
    "pharmacy": format_pharmacy_bill,
}


def format_text(raw_text: str) -> str:
    """
    Clean, classify, and format raw OCR text into a readable string.

    Args:
        raw_text: Raw text as returned by `ocr_service.extract_text`.

    Returns:
        A formatted, human-readable string: a tabulated report for
        lab/prescription/pharmacy documents, or a readability-improved
        version of the text for anything else.
    """
    if not raw_text or not raw_text.strip():
        logger.warning("format_text received empty input.")
        return "No text was extracted from this document."

    cleaned = clean_text(raw_text)
    document_type = detect_document_type(cleaned)
    logger.info("Detected document type: %s", document_type)

    formatter_func = _FORMATTER_DISPATCH.get(document_type, format_generic)
    formatted = formatter_func(cleaned)

    return formatted