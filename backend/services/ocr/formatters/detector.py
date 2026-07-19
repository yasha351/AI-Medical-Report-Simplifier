"""
detector.py
------------
Detects the *type* of a medical document from its raw OCR text using
generic keyword-frequency scoring.

Supported document types:
    - "lab"          : Laboratory / blood test reports
    - "prescription" : Doctor prescriptions
    - "pharmacy"      : Pharmacy bills / invoices
    - "generic"       : Fallback when no type scores confidently

Design notes:
    - No machine learning is used — this is pure, deterministic keyword
      scoring, as required.
    - Keywords are generic *document vocabulary* (structural terms that
      appear across virtually all documents of a given type), never
      specific test names, medicine names, or hospital names. For
      example "reference range" and "specimen" are used for lab
      reports instead of "Hemoglobin" or "Platelets".
    - Matching is case-insensitive and uses word boundaries so that,
      e.g., "tab" doesn't spuriously match inside an unrelated word.
"""

import re
from collections import Counter
from typing import Dict, List, Set

# --------------------------------------------------------------------------
# Generic keyword sets per document type.
#
# These are intentionally broad, structural/vocabulary terms that show
# up across many different hospitals, labs, and pharmacies — never
# specific instances (no test names, no drug brand names, no hospital
# names).
# --------------------------------------------------------------------------

LAB_KEYWORDS: Set[str] = {
    "test",
    "test name",
    "result",
    "results",
    "reference range",
    "normal range",
    "range",
    "specimen",
    "sample",
    "units",
    "unit",
    "laboratory",
    "lab report",
    "pathology",
    "investigation",
    "biochemistry",
    "hematology",
    "haematology",
    "reported on",
    "collected on",
    "method",
    "value",
}

PRESCRIPTION_KEYWORDS: Set[str] = {
    "prescription",
    "rx",
    "dosage",
    "dose",
    "frequency",
    "duration",
    "tab",
    "tablet",
    "cap",
    "capsule",
    "syrup",
    "injection",
    "route",
    "sig",
    "od",
    "bd",
    "tds",
    "qid",
    "hs",
    "sos",
    "prn",
    "morning",
    "afternoon",
    "night",
    "before food",
    "after food",
    "days",
    "diagnosis",
    "advice",
    "follow up",
    "chief complaint",
}

PHARMACY_KEYWORDS: Set[str] = {
    "bill",
    "invoice",
    "receipt",
    "gst",
    "gstin",
    "particulars",
    "qty",
    "quantity",
    "mrp",
    "rate",
    "amount",
    "total",
    "net amount",
    "gross amount",
    "discount",
    "batch",
    "batch no",
    "expiry",
    "hsn",
    "store",
    "pharmacy",
    "cashier",
    "payment mode",
    "paid",
    "balance",
}

# Priority order used to break ties when two categories score equally.
# Ordered from most structurally specific to least, so a document that
# ambiguously mentions both lab and prescription vocabulary leans lab
# (labs rarely mention dosage terms, whereas prescriptions sometimes
# reference test-like words).
_TIE_BREAK_ORDER: List[str] = ["lab", "prescription", "pharmacy"]

# Minimum keyword-hit count required before a document is confidently
# classified as anything other than "generic". This avoids
# misclassifying short or noisy OCR output on a single stray match.
_MIN_SCORE_THRESHOLD: int = 3


def _count_keyword_hits(text: str, keywords: Set[str]) -> int:
    """
    Count how many times any keyword from `keywords` appears in `text`,
    using whole-word/phrase, case-insensitive matching.

    Args:
        text: The text to search (typically raw or cleaned OCR output).
        keywords: Set of keyword phrases to search for.

    Returns:
        Total number of keyword occurrences found (a single keyword can
        match multiple times).
    """
    lowered_text = text.lower()
    total_hits = 0

    for keyword in keywords:
        # Build a word-boundary pattern that also works for multi-word
        # phrases (e.g. "reference range").
        pattern = r"\b" + re.escape(keyword) + r"\b"
        matches = re.findall(pattern, lowered_text)
        total_hits += len(matches)

    return total_hits


def score_document(text: str) -> Dict[str, int]:
    """
    Compute a keyword-hit score for every supported document type.

    Args:
        text: Raw or cleaned OCR text.

    Returns:
        Dictionary mapping document type name ("lab", "prescription",
        "pharmacy") to its integer keyword-hit score.
    """
    scores: Dict[str, int] = {
        "lab": _count_keyword_hits(text, LAB_KEYWORDS),
        "prescription": _count_keyword_hits(text, PRESCRIPTION_KEYWORDS),
        "pharmacy": _count_keyword_hits(text, PHARMACY_KEYWORDS),
    }
    return scores


def detect_document_type(text: str) -> str:
    """
    Detect the document type of a piece of raw OCR text.

    Algorithm:
        1. Score the text against each known category's keyword set.
        2. Pick the category with the highest score.
        3. If the highest score is below `_MIN_SCORE_THRESHOLD`, or the
           text is empty/whitespace, fall back to "generic".
        4. Ties are broken using a fixed priority order.

    Args:
        text: Raw or cleaned OCR text extracted from a medical document.

    Returns:
        One of "lab", "prescription", "pharmacy", or "generic".
    """
    if not text or not text.strip():
        return "generic"

    scores = score_document(text)
    counter = Counter(scores)
    highest_score = max(counter.values())

    if highest_score < _MIN_SCORE_THRESHOLD:
        return "generic"

    # Collect every category that achieved the highest score, then
    # break ties using the fixed priority order.
    top_categories = [category for category, score in counter.items()
                       if score == highest_score]

    for category in _TIE_BREAK_ORDER:
        if category in top_categories:
            return category

    # Should not normally be reached, but guarantees a safe fallback.
    return "generic"