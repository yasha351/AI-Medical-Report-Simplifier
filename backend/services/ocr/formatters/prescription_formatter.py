"""
prescription_formatter.py
---------------------------
Formats raw OCR text from **doctor prescriptions** into a clean tabular
string.

Real-world prescriptions vary a lot in how they express dosage, so this
module recognizes several generic (non-hospital-specific) shapes:

    - Numeric dosage codes:    "1-0-1", "0.5-0-0.5"
    - Frequency abbreviations: "OD", "BD", "TDS", "HS", "SOS", ...
    - Written-out schedules:   "1 Morning, 1 Night",
                                "1/2 Morning, 1/2 Night"
                                (any "<number/fraction> <time-of-day>"
                                combination — Morning/Afternoon/Evening/
                                Night/Noon/Bedtime are generic time-of-day
                                words, not specific medicine/hospital
                                vocabulary)

And several generic layout quirks:

    - Item-number prefixes before the medicine name, e.g. "1}", "2)",
      "3."
    - Parenthetical annotation lines that should be ignored when
      looking for the next dosage/duration, e.g. "(Before Food)",
      "(Tot:20 Tab)"

Two extraction passes are used:

    1. A strict single-line regex for the classic clean layout:
       "<medicine>  <dosage>  [duration]" all on one line.
    2. A tolerant multi-line scan for the (very common) layout where
       medicine name, dosage, and duration are on separate lines, with
       optional annotation lines interspersed.
"""

import re
from typing import List, Optional, Tuple

from tabulate import tabulate

# --------------------------------------------------------------------------
# Generic, shape-based regular expressions.
# --------------------------------------------------------------------------

# Numeric dosage code, e.g. "1-0-1", "0.5-0-0.5"
_DOSAGE_NUMERIC_RE = re.compile(r"\d+(\.\d+)?\s*-\s*\d+(\.\d+)?\s*-\s*\d+(\.\d+)?")

# Generic pharmacology frequency abbreviations (structural shorthand,
# not specific medicine names).
_DOSAGE_ABBR_RE = re.compile(
    r"\b(OD|BD|TDS|QID|HS|SOS|STAT|PRN|AC|PC|Q\d+H)\b", re.IGNORECASE
)

# Generic time-of-day words used in written-out dosage schedules.
# These describe *when* a dose is taken, universally, regardless of
# hospital or medicine — analogous to "OD"/"BD" abbreviations.
_TIME_OF_DAY_RE = re.compile(
    r"\d+(?:/\d+)?\s*[-,]?\s*(morning|afternoon|evening|night|noon|bedtime)",
    re.IGNORECASE,
)

# A duration phrase anywhere in a line, e.g. "5 Days", "2 Weeks"
_DURATION_RE = re.compile(
    r"\d+\s*(day|days|week|weeks|month|months)", re.IGNORECASE
)

# A dosage token usable inside the strict single-line regex.
_DOSAGE_TOKEN = (
    r"(?:\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?"
    r"|OD|BD|TDS|QID|HS|SOS|STAT|PRN|AC|PC|Q\d+H)"
)

# Strict single-line row: "<medicine> <dosage> [duration]", all one line.
_SINGLE_LINE_ROW_RE = re.compile(
    rf"^(?P<medicine>[A-Za-z][A-Za-z0-9\s\.\-/%()]*?)\s{{1,}}"
    rf"(?P<dosage>{_DOSAGE_TOKEN})"
    rf"(?:\s{{1,}}(?P<duration>\d+\s*(?:day|days|week|weeks|month|months)))?\s*$",
    re.IGNORECASE,
)

# Leading item-number marker before a medicine name, e.g. "1}", "2)", "3."
_LEADING_MARKER_RE = re.compile(r"^\d+\s*[\}\)\.\-]\s*")

# A parenthetical annotation line, e.g. "(Before Food)", "(Tot:20 Tab)"
_ANNOTATION_RE = re.compile(r"^\(.*\)\.?\s*$")

# Generic structural header vocabulary, used only to skip header rows.
_HEADER_WORDS = {
    "medicine", "medicines", "drug", "dosage", "dose", "frequency",
    "duration", "days", "sig", "route", "instructions", "quantity", "name",
}

_TABLE_HEADERS: List[str] = ["Medicine", "Dosage", "Duration"]
_DEFAULT_DURATION = "-"


def _clean_line(line: str) -> str:
    """Collapse internal whitespace and strip a single line."""
    return re.sub(r"[ \t]+", " ", line).strip()


def _is_annotation_line(line: str) -> bool:
    """Return True for a parenthetical note line, e.g. "(Before Food)"."""
    return bool(_ANNOTATION_RE.match(line))


def _is_dosage_line(line: str) -> bool:
    """
    Return True if a line contains a dosage signal anywhere in it:
    a numeric triplet code, a frequency abbreviation, or a written
    "<number> <time-of-day>" schedule fragment.
    """
    return bool(
        _DOSAGE_NUMERIC_RE.search(line)
        or _DOSAGE_ABBR_RE.search(line)
        or _TIME_OF_DAY_RE.search(line)
    )


def _is_duration_line(line: str) -> bool:
    """Return True if a line contains a duration phrase anywhere in it."""
    return bool(_DURATION_RE.search(line))


def _looks_like_header(line: str) -> bool:
    """
    Heuristically detect a column-header line (e.g. "Medicine Name",
    "Dosage", "Duration") so it can be skipped. Based on generic
    structural vocabulary, not specific medicine names. A line with any
    digit in it is never treated as a header, since real dosage/duration
    data always contains digits.
    """
    lowered = line.lower()
    words = set(re.findall(r"[a-z]+", lowered))
    has_header_word = bool(words & _HEADER_WORDS)
    has_number = bool(re.search(r"\d", line))
    return has_header_word and not has_number


def _strip_leading_marker(line: str) -> str:
    """Remove a leading item-number marker like '1}', '2)', '3.' if present."""
    return _LEADING_MARKER_RE.sub("", line).strip()


def _is_standalone_row_line(line: str) -> bool:
    """
    Return True if a line is already a complete, self-contained
    "medicine dosage [duration]" row on its own. Used to prevent the
    tolerant multi-line lookahead from accidentally swallowing the
    *next* medicine's entire entry just because it happens to contain a
    dosage or duration phrase somewhere in it.
    """
    return _SINGLE_LINE_ROW_RE.match(line) is not None


def _extract_single_line_row(line: str) -> Optional[Tuple[str, str, str]]:
    """Try to parse one line as a complete 'medicine dosage [duration]' row."""
    match = _SINGLE_LINE_ROW_RE.match(line)
    if not match:
        return None
    duration = match.group("duration") or _DEFAULT_DURATION
    return match.group("medicine").strip(), match.group("dosage").strip(), duration


def extract_medicine_rows(text: str) -> List[Tuple[str, str, str]]:
    """
    Scan cleaned OCR text and extract (medicine, dosage, duration) rows.

    Two passes are tried per position:
        1. Strict single-line "medicine dosage [duration]" match.
        2. Tolerant multi-line scan: treat the current line as a
           medicine-name candidate, then look ahead (skipping any
           parenthetical annotation lines) for the next dosage line and
           then the next duration line.

    Args:
        text: Raw or lightly cleaned OCR text.

    Returns:
        List of (medicine, dosage, duration) tuples, in the order they
        were found. `duration` is `"-"` when not detected.
    """
    raw_lines = [_clean_line(line) for line in text.splitlines()]
    lines = [line for line in raw_lines if line]  # drop blank lines

    rows: List[Tuple[str, str, str]] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if _is_annotation_line(line) or _looks_like_header(line):
            i += 1
            continue

        # --- Pass 1: strict single-line row ---
        single_match = _extract_single_line_row(line)
        if single_match:
            rows.append(single_match)
            i += 1
            continue

        # A line that is itself only a dosage or duration fragment (no
        # medicine name attached) can't start a new row on its own.
        if _is_dosage_line(line) or _is_duration_line(line):
            i += 1
            continue

        # --- Pass 2: tolerant multi-line scan ---
        if re.search(r"[A-Za-z]", line):
            medicine = _strip_leading_marker(line)
            j = i + 1

            while j < n and _is_annotation_line(lines[j]):
                j += 1

            dosage: Optional[str] = None
            if (
                j < n
                and _is_dosage_line(lines[j])
                and not _is_standalone_row_line(lines[j])
            ):
                dosage = lines[j]
                j += 1

            while j < n and _is_annotation_line(lines[j]):
                j += 1

            duration = _DEFAULT_DURATION
            if (
                j < n
                and _is_duration_line(lines[j])
                and not _is_standalone_row_line(lines[j])
            ):
                duration = lines[j]
                j += 1

            if dosage:
                rows.append((medicine, dosage, duration))
                i = j
                continue

        # No pattern matched at this position; move on without losing
        # the line (it simply isn't recognized as part of a medicine row).
        i += 1

    return rows


def format_prescription(text: str) -> str:
    """
    Format raw OCR text from a prescription into a readable, numbered
    table string.

    Args:
        text: Raw (or cleaned) OCR text believed to be a prescription.

    Returns:
        A tabulated string of extracted medicine rows. If no rows could
        be confidently detected, returns a short notice followed by the
        original text (so no information is silently lost).
    """
    rows = extract_medicine_rows(text)

    if not rows:
        return (
            "No medicine rows could be automatically detected.\n\n"
            "Original OCR text:\n" + text.strip()
        )

    table = tabulate(rows, headers=_TABLE_HEADERS, tablefmt="presto")
    return table