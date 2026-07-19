"""
prescription_formatter.py
---------------------------
Formats raw OCR text from **doctor prescriptions** into a clean tabular
string.

Extraction strategy (shape-based, no hardcoded medicine names):

A prescription line always has the same underlying shape:

    <medicine name (free text)>  <dosage code>  [duration]

Where a "dosage code" is either a numeric pattern like "1-0-1" or a
short frequency abbreviation like "OD", "BD", "TDS", "HS", "SOS", and
"duration" is an optional trailing phrase like "5 Days" or "2 Weeks".

This shape can appear across three common OCR layouts, handled by a
sliding window (mirroring `lab_formatter`'s approach):

    1. Single line:  "TAB PARACETAMOL 650 MG   1-0-1   5 Days"
    2. Two lines:     "TAB PARACETAMOL 650 MG"
                       "1-0-1"
    3. Three lines:   "TAB PARACETAMOL 650 MG"
                       "1-0-1"
                       "5 Days"
"""

import re
from typing import List, Optional, Tuple

from tabulate import tabulate

# --------------------------------------------------------------------------
# Generic, shape-based regular expressions.
# --------------------------------------------------------------------------

# Numeric dosage code, e.g. "1-0-1", "0.5-0-0.5"
_DOSAGE_NUMERIC_RE = re.compile(r"^\d+(\.\d+)?\s*-\s*\d+(\.\d+)?\s*-\s*\d+(\.\d+)?$")

# Generic pharmacology frequency abbreviations (structural shorthand,
# not specific medicine names).
_DOSAGE_ABBR_RE = re.compile(
    r"^(OD|BD|TDS|QID|HS|SOS|STAT|PRN|AC|PC|Q\d+H)$", re.IGNORECASE
)

# A standalone duration phrase, e.g. "5 Days", "2 Weeks", "1 Month"
_DURATION_RE = re.compile(
    r"^\d+\s*(day|days|week|weeks|month|months)$", re.IGNORECASE
)

# A dosage token usable inside a combined regex (either form).
_DOSAGE_TOKEN = (
    r"(?:\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?"
    r"|OD|BD|TDS|QID|HS|SOS|STAT|PRN|AC|PC|Q\d+H)"
)

# Generic "time-of-day schedule" dosage shape, e.g. "1 Morning, 1 Night"
# or "1/2 Morning, 1/2 Night". This is structural (count + free word,
# repeated with commas) rather than a fixed vocabulary, so it still
# matches OCR-garbled spellings like "Motning"/"Moming"/"Momung". The
# leading count also accepts a bare "I" or "l", since OCR very commonly
# misreads a handwritten/printed "1" as a capital I or lowercase L.
_SCHEDULE_COUNT = r"(?:\d+(?:/\d+)?|[Il])"
_SCHEDULE_DOSAGE_RE = re.compile(
    rf"^{_SCHEDULE_COUNT}\s+[A-Za-z]+\.?"
    rf"(?:,\s*{_SCHEDULE_COUNT}\s+[A-Za-z]+\.?)+\.?$"
)

# A leading list marker such as "1}", "2)", "3.", "(4)" in front of a
# medicine name. Stripped before display since the row is already
# numbered by `format_prescription`.
_LIST_MARKER_RE = re.compile(r"^\(?\d+\)?[.)}]\s*")

# A trailing instruction/total note such as "(Before Food)" or
# "(Tot:20 Tab)". Detected generically by the presence of a parenthesized
# segment, tolerating leading OCR noise like stray dots/underscores.
_NOTE_LINE_RE = re.compile(r"\(.*\)")

# Full single-line row: "<medicine> <dosage> [duration]"
_SINGLE_LINE_ROW_RE = re.compile(
    rf"^(?P<medicine>[A-Za-z][A-Za-z0-9\s\.\-/%()]*?)\s{{1,}}"
    rf"(?P<dosage>{_DOSAGE_TOKEN})"
    rf"(?:\s{{1,}}(?P<duration>\d+\s*(?:day|days|week|weeks|month|months)))?\s*$",
    re.IGNORECASE,
)

# A line that is "<dosage> <duration>" combined (used for the 2-line
# layout where line 2 holds both dosage and duration).
_DOSAGE_AND_DURATION_RE = re.compile(
    rf"^(?P<dosage>{_DOSAGE_TOKEN})\s+"
    rf"(?P<duration>\d+\s*(?:day|days|week|weeks|month|months))$",
    re.IGNORECASE,
)

# Generic structural header vocabulary, used only to skip header rows.
_HEADER_WORDS = {
    "medicine", "medicines", "drug", "dosage", "dose", "frequency",
    "duration", "days", "sig", "route", "instructions", "quantity",
}

_TABLE_HEADERS: List[str] = ["No", "Medicine", "Dosage", "Duration"]
_DEFAULT_DURATION = "-"


def _clean_line(line: str) -> str:
    """Collapse internal whitespace and strip a single line."""
    return re.sub(r"[ \t]+", " ", line).strip()


def _is_dosage_line(line: str) -> bool:
    """Return True if a line is entirely a dosage code, abbreviation, or
    free-text time-of-day schedule (e.g. "1 Morning, 1 Night")."""
    return bool(
        _DOSAGE_NUMERIC_RE.match(line)
        or _DOSAGE_ABBR_RE.match(line)
        or _SCHEDULE_DOSAGE_RE.match(line)
    )


def _looks_like_note(line: str) -> bool:
    """
    Return True if a line is a trailing instruction/total note rather
    than a new medicine label, e.g. "(Before Food)" or "(Tot:20 Tab)",
    even with stray leading OCR noise like "..(Before Food)".

    Detected generically by the presence of a parenthesized segment, so
    it never depends on specific instruction wording.
    """
    return bool(_NOTE_LINE_RE.search(line))


def _strip_list_marker(line: str) -> str:
    """Remove a leading list marker such as "1}", "2)", "(3)" if present."""
    return _LIST_MARKER_RE.sub("", line, count=1).strip()


def _consume_trailing_notes(lines: List[str], start: int) -> Tuple[str, int]:
    """
    Greedily collect consecutive trailing note lines (parenthesized
    instructions/totals) starting at `start`.

    Args:
        lines: Full list of cleaned lines.
        start: Index to begin scanning from.

    Returns:
        A tuple of (joined note text, index just past the last note
        line consumed). The joined text is "" if no notes were found.
    """
    notes: List[str] = []
    i = start
    n = len(lines)

    while i < n and _looks_like_note(lines[i]) and not _is_dosage_line(lines[i]):
        # Strip stray leading OCR noise (e.g. "..", "_.") before the
        # actual parenthesized content.
        notes.append(re.sub(r"^[^A-Za-z0-9(]+", "", lines[i]))
        i += 1

    return " ".join(notes), i


def _is_duration_line(line: str) -> bool:
    """Return True if a line is entirely a duration phrase."""
    return bool(_DURATION_RE.match(line))


def _looks_like_header(line: str) -> bool:
    """
    Heuristically detect a column-header line (e.g. "Medicine Dosage
    Duration") so it can be skipped. Based on generic structural
    vocabulary, not specific medicine names.

    Args:
        line: A single cleaned line.

    Returns:
        True if the line looks like a table header rather than data.
    """
    lowered = line.lower()
    words = set(re.findall(r"[a-z]+", lowered))
    has_header_word = bool(words & _HEADER_WORDS)
    has_number = bool(re.search(r"\d", line))
    is_dosage_or_duration = _is_dosage_line(line) or _is_duration_line(line)
    # A genuine header row (e.g. "Medicine Dosage Duration") has no
    # digits at all. A real data line that merely happens to contain a
    # word like "Days" (e.g. "...OD 10 Days") must NOT be treated as a
    # header just because "Days" overlaps with the header vocabulary.
    return has_header_word and not has_number and not is_dosage_or_duration


def _is_label_line(line: str) -> bool:
    """
    A "label" line is free text that isn't itself a dosage code or
    duration phrase — i.e. it could plausibly be a medicine name.

    Args:
        line: A single cleaned line.

    Returns:
        True if the line looks like it could be a medicine-name label.
    """
    if not line:
        return False
    if _is_dosage_line(line) or _is_duration_line(line):
        return False
    return bool(re.search(r"[A-Za-z]", line))


def extract_medicine_rows(text: str) -> List[Tuple[str, str, str]]:
    """
    Scan cleaned OCR text and extract (medicine, dosage, duration) rows
    using a sliding window that tries the single-line, two-line, and
    three-line layouts described in the module docstring.

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

        if _looks_like_header(line):
            i += 1
            continue

        # --- Strategy 1: single line "medicine dosage [duration]" ---
        single_match = _SINGLE_LINE_ROW_RE.match(line)
        if single_match:
            duration = single_match.group("duration") or _DEFAULT_DURATION
            notes, next_i = _consume_trailing_notes(lines, i + 1)
            if notes:
                duration = notes if duration == _DEFAULT_DURATION else f"{duration} {notes}"
            rows.append(
                (_strip_list_marker(single_match.group("medicine")),
                 single_match.group("dosage").strip(),
                 duration)
            )
            i = next_i
            continue

        # --- Strategy 3: three lines: medicine / dosage / duration ---
        if (
            i + 2 < n
            and _is_label_line(line)
            and _is_dosage_line(lines[i + 1])
            and _is_duration_line(lines[i + 2])
        ):
            notes, next_i = _consume_trailing_notes(lines, i + 3)
            duration = f"{lines[i + 2]} {notes}".strip()
            rows.append((_strip_list_marker(line), lines[i + 1], duration))
            i = next_i
            continue

        # --- Strategy 2b: two lines: medicine / "dosage duration" ---
        if i + 1 < n and _is_label_line(line):
            combined_match = _DOSAGE_AND_DURATION_RE.match(lines[i + 1])
            if combined_match:
                notes, next_i = _consume_trailing_notes(lines, i + 2)
                duration = f"{combined_match.group('duration')} {notes}".strip()
                rows.append(
                    (_strip_list_marker(line), combined_match.group("dosage"), duration)
                )
                i = next_i
                continue

        # --- Strategy 2a: two lines: medicine / dosage (no duration) ---
        if i + 1 < n and _is_label_line(line) and _is_dosage_line(lines[i + 1]):
            notes, next_i = _consume_trailing_notes(lines, i + 2)
            duration = notes if notes else _DEFAULT_DURATION
            rows.append((_strip_list_marker(line), lines[i + 1], duration))
            i = next_i
            continue

        # No pattern matched at this position; move on without losing
        # the line (it simply isn't recognized as a medicine row).
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

    numbered_rows = [
        (index + 1, medicine, dosage, duration)
        for index, (medicine, dosage, duration) in enumerate(rows)
    ]

    table = tabulate(numbered_rows, headers=_TABLE_HEADERS, tablefmt="grid")
    return table