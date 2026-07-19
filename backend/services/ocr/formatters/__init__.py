"""
formatters
-----------
Document-type-aware formatting layer for the AI Medical Report
Simplifier's OCR output.

Exposes the document type detector and each specialized formatter for
convenient importing, e.g.:

    from formatters import detect_document_type, format_lab_report
"""

from .detector import detect_document_type, score_document
from .generic_formatter import clean_text, format_generic
from .lab_formatter import extract_lab_rows, format_lab_report
from .pharmacy_formatter import (
    extract_bill_items,
    extract_header_info,
    format_pharmacy_bill,
)
from .prescription_formatter import extract_medicine_rows, format_prescription

__all__ = [
    "detect_document_type",
    "score_document",
    "clean_text",
    "format_generic",
    "extract_lab_rows",
    "format_lab_report",
    "extract_bill_items",
    "extract_header_info",
    "format_pharmacy_bill",
    "extract_medicine_rows",
    "format_prescription",
]