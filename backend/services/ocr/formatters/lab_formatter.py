"""
lab_formatter.py
------------------
Formats raw OCR text from **laboratory / blood test reports** into a
clean tabular string.

Extraction strategy (all pattern/shape based — no hardcoded test names):

A lab result row always has the same underlying shape, regardless of
which hospital produced it:

    <test name (free text)>  <numeric result>  <numeric reference range>

This shape can appear in OCR output in three common layouts:

    1. Single line:   "Hemoglobin        7.4        11.5-13.5"
    2. Two lines:      "Hemoglobin"
                        "7.4 11.5-13.5"
    3. Three lines:     "Hemoglobin"
                        "7.4"
                        "11.5-13.5"

`extract_lab_rows` scans the text with a sliding window and tries each
layout in turn, so it works regardless of which one a given OCR engine
happened to produce.
"""

import re
from typing import List, Optional, Tuple

from tabulate import tabulate

# --------------------------------------------------------------------------
# Generic, shape-based regular expressions (no hospital-specific terms).
# --------------------------------------------------------------------------

# A standalone numeric value, e.g. "7.4", "56", "10.5"
_NUMBER_ONLY_RE = re.compile(r"^\d+(\.\d+)?$")

# A standalone numeric range, e.g. "11.5-13.5", "150-450", "4000 - 11000"
_RANGE_ONLY_RE = re.compile(r"^\d+(\.\d+)?\s*-\s*\d+(\.\d+)?$")

# A line that is entirely "<value><whitespace><range>", e.g.
# "7.4 11.5-13.5"
_VALUE_AND_RANGE_RE = re.compile(
    r"^(?P<value>\d+(\.\d+)?)\s+(?P<range>\d+(\.\d+)?\s*-\s*\d+(\.\d+)?)$"
)

# A full single-line row: "<label> <value> <range>", with the label
# being any free text that doesn't start with a digit.
_SINGLE_LINE_ROW_RE = re.compile(
    r"^(?P<label>[A-Za-z][A-Za-z0-9\s\.\-/%()]*?)\s{1,}"
    r"(?P<value>\d+(\.\d+)?)\s{1,}"
    r"(?P<range>\d+(\.\d+)?\s*-\s*\d+(\.\d+)?)\s*$"
)

# Generic structural header vocabulary used only to *skip* header rows,
# never to identify data. These words describe columns, not tests.
_HEADER_WORDS = {"test", "result", "value", "range", "normal", "reference", "name", "unit", "units"}

_TABLE_HEADERS: List[str] = ["Test Name", "Result", "Reference Range"]


def _clean_line(line: str) -> str:
    """Collapse internal whitespace and strip a single line."""
    return re.sub(r"[ \t]+", " ", line).strip()


def _looks_like_header(line: str) -> bool:
    """
    Heuristically detect a column-header line (e.g. "Test Name Result
    Reference Range") so it can be skipped during row extraction. Based
    purely on generic structural vocabulary, not specific test names.

    Args:
        line: A single cleaned line.

    Returns:
        True if the line looks like a table header rather than a data
        row (i.e. it contains header vocabulary and no numeric value).
    """
    lowered = line.lower()
    words = set(re.findall(r"[a-z]+", lowered))
    has_header_word = bool(words & _HEADER_WORDS)
    has_number = bool(re.search(r"\d", line))
    return has_header_word and not has_number


def _is_label_line(line: str) -> bool:
    """
    A "label" line is free text that is neither a bare number nor a bare
    range — i.e. it could plausibly be a test name.

    Args:
        line: A single cleaned line.

    Returns:
        True if the line looks like it could be a test-name label.
    """
    if not line:
        return False
    if _NUMBER_ONLY_RE.match(line) or _RANGE_ONLY_RE.match(line):
        return False
    if not re.search(r"[A-Za-z]", line):
        return False
    return True


def _extract_single_line_row(line: str) -> Optional[Tuple[str, str, str]]:
    """Try to parse one line as a complete "label value range" row."""
    match = _SINGLE_LINE_ROW_RE.match(line)
    if match:
        return (
            match.group("label").strip(),
            match.group("value").strip(),
            match.group("range").strip(),
        )
    return None


def extract_lab_rows(text: str) -> List[Tuple[str, str, str]]:
    """
    Scan cleaned OCR text and extract (test_name, result, reference_range)
    rows using a sliding window that tries the single-line, two-line, and
    three-line layouts described in the module docstring.

    Args:
        text: Raw or lightly cleaned OCR text.

    Returns:
        List of (test_name, result, reference_range) tuples, in the
        order they were found.
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

        # --- Strategy 1: single line "label value range" ---
        single_match = _extract_single_line_row(line)
        if single_match:
            rows.append(single_match)
            i += 1
            continue

        # --- Strategy 3: three lines: label / value / range ---
        if (
            i + 2 < n
            and _is_label_line(line)
            and _NUMBER_ONLY_RE.match(lines[i + 1])
            and _RANGE_ONLY_RE.match(lines[i + 2])
        ):
            rows.append((line, lines[i + 1], lines[i + 2]))
            i += 3
            continue

        # --- Strategy 2: two lines: label / "value range" ---
        if i + 1 < n and _is_label_line(line):
            combined_match = _VALUE_AND_RANGE_RE.match(lines[i + 1])
            if combined_match:
                rows.append(
                    (
                        line,
                        combined_match.group("value"),
                        combined_match.group("range"),
                    )
                )
                i += 2
                continue

        # No pattern matched at this position; move on without losing
        # the line (it simply isn't recognized as a lab-result row).
        i += 1

    return rows


def format_lab_report(text: str) -> str:
    """
    Format raw OCR text from a lab report into a readable table string.

    Args:
        text: Raw (or cleaned) OCR text believed to be a lab report.

    Returns:
        A tabulated string of extracted test rows. If no rows could be
        confidently detected, returns a short notice followed by the
        original text (so no information is silently lost).
    """
    rows = extract_lab_rows(text)

    if not rows:
        return (
            "No lab result rows could be automatically detected.\n\n"
            "Original OCR text:\n" + text.strip()
        )

    table = tabulate(rows, headers=_TABLE_HEADERS, tablefmt="grid")
    return table