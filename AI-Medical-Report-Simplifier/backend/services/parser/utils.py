"""
utils.py
--------

Helper functions used by parser.py:

- Text cleaning / normalization
- Line filtering (dropping headers, addresses, comments, etc.)
- Patient metadata extraction (name / age / gender)
- Regex-based extraction of a test name, numeric value, and unit
  from a single line of OCR text.

Nothing here depends on OCR or Gemini implementations, keeping this
module reusable and independently testable.
"""

import re
from typing import List, Optional, Tuple, Union

from models import LabTest

# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

# Collapses any run of whitespace (spaces, tabs) into a single space.
_WHITESPACE_RE = re.compile(r"[ \t]+")


def clean_text(text: str) -> str:
    """
    Normalize raw OCR text: collapse repeated whitespace, strip
    leading/trailing blank lines, and standardize line endings.
    """
    if not text:
        return ""

    # Normalize Windows / Mac line endings to \n
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.strip()


def split_lines(text: str) -> List[str]:
    """
    Split cleaned text into a list of non-empty, whitespace-collapsed
    lines, ready for line-by-line processing.
    """
    lines = []
    for raw_line in text.split("\n"):
        collapsed = _WHITESPACE_RE.sub(" ", raw_line).strip()
        if collapsed:
            lines.append(collapsed)
    return lines


# ---------------------------------------------------------------------------
# Line filtering
# ---------------------------------------------------------------------------

# Keywords that indicate a line is metadata/noise rather than a test
# result. Matched case-insensitively against the start of the line.
_IGNORABLE_KEYWORDS = (
    "hospital",
    "doctor",
    "dr.",
    "address",
    "reference range",
    "ref range",
    "ref. range",
    "comment",
    "report date",
    "collected",
    "collection",
    "sample id",
    "lab id",
    "signature",
    "authorized",
)

# Keywords that indicate patient metadata, handled by
# extract_patient_info() rather than being treated as test lines.
_PATIENT_FIELD_PATTERNS = {
    "name": re.compile(r"(?:patient\s*name|patient|name)\s*[:\-]\s*(.+)", re.IGNORECASE),
    "age": re.compile(r"age\s*[:\-]\s*(\d+)", re.IGNORECASE),
    "gender": re.compile(r"(?:gender|sex)\s*[:\-]\s*([A-Za-z]+)", re.IGNORECASE),
}


def is_ignorable_line(line: str) -> bool:
    """
    Return True if the line matches known non-test metadata such as
    hospital name, doctor, address, reference ranges, or comments.
    """
    lower = line.lower()
    return any(keyword in lower for keyword in _IGNORABLE_KEYWORDS)


def is_patient_info_line(line: str) -> bool:
    """Return True if the line matches a known patient-info field."""
    return any(pattern.search(line) for pattern in _PATIENT_FIELD_PATTERNS.values())


def extract_patient_field(line: str) -> Optional[Tuple[str, str]]:
    """
    Try to extract a (field_name, value) pair such as
    ("name", "John Doe") from a line of OCR text.

    Returns None if the line doesn't match any known patient field.
    """
    for field_name, pattern in _PATIENT_FIELD_PATTERNS.items():
        match = pattern.search(line)
        if match:
            return field_name, match.group(1).strip()
    return None


# ---------------------------------------------------------------------------
# Test-line parsing
# ---------------------------------------------------------------------------

# Matches lines like:
#   "Hemoglobin      10.2 g/dL"
#   "WBC             6200 /uL"
#   "Hb 10.2 g/dL"
#   "Platelets 250000"          (unit optional)
#   "Hemoglobin 10.2 g/dL 13.0 - 17.0"  (trailing reference range ignored)
#
# Group 1: test name (letters, digits, spaces, dots, parens, hyphens, slash)
# Group 2: numeric value (int or float, optionally signed)
# Group 3: unit (optional token; stops at the next digit so a trailing
#          reference range like "13.0 - 17.0" is not swallowed)
#
# Note: deliberately NOT anchored with `$` at the end -- only the
# name/value/unit prefix of the line is captured, and anything after
# (e.g. a reference range column) is ignored.
_TEST_LINE_RE = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9\.\-\(\)/ ]*?)"
    r"\s+"
    r"(?P<value>[-+]?\d+(?:\.\d+)?)"
    r"\s*"
    r"(?P<unit>[A-Za-z%°µ/\^]*)"
)


def parse_numeric_value(raw_value: str) -> Optional[Union[int, float]]:
    """
    Convert a raw numeric string into an int or float.
    Returns None if the string isn't a valid number.
    """
    try:
        if "." in raw_value:
            return float(raw_value)
        return int(raw_value)
    except (ValueError, TypeError):
        return None


def extract_test_from_line(line: str) -> Optional[LabTest]:
    """
    Attempt to extract a LabTest (name, value, unit) from a single
    cleaned line of OCR text.

    Returns None if the line doesn't look like a valid test result
    (e.g. malformed OCR text, missing numeric value).
    """
    match = _TEST_LINE_RE.match(line)
    if not match:
        return None

    raw_name = match.group("name").strip()
    raw_value = match.group("value").strip()
    raw_unit = match.group("unit").strip()

    value = parse_numeric_value(raw_value)
    if value is None:
        return None

    if not raw_name:
        return None

    return LabTest(name=raw_name, value=value, unit=raw_unit)
