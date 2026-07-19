"""
pharmacy_formatter.py
-----------------------
Formats raw OCR text from **pharmacy bills / invoices** into a clean
tabular string, plus a separately extracted header-info block.

Extraction strategy (shape-based, no hardcoded medicine/store names):

A bill line item always has the same underlying shape:

    <particulars (free text)>  <3 or more trailing numeric columns>

The trailing numeric columns typically represent some combination of
Qty, MRP, Rate, and Amount. Since column *count* varies by bill layout,
this module maps trailing numbers to (qty, rate, amount) generically by
position:

    - exactly 3 numbers  -> (qty, rate, amount)
    - exactly 4 numbers  -> (qty, <ignored>, rate, amount)
    - 5+ numbers         -> qty = first, amount = last,
                             rate = second-to-last, extras ignored

Header information (patient, bill no, GSTIN, date, store, doctor, etc.)
is extracted generically from any `"label: value"` line — no fixed list
of expected labels is required, so this works regardless of which
fields a particular pharmacy chooses to print.
"""

import re
from typing import Dict, List, Optional, Tuple

from tabulate import tabulate

# --------------------------------------------------------------------------
# Generic, shape-based regular expressions.
# --------------------------------------------------------------------------

# A generic numeric column value: integer, optionally with thousands
# separators and/or up to 2 decimal places.
_NUMERIC_COLUMN_RE = re.compile(r"^\d{1,3}(,\d{2,3})*(\.\d{1,2})?$")

# A small standalone integer, commonly a leading serial number (S.No).
_SMALL_INT_RE = re.compile(r"^\d{1,3}$")

_TABLE_HEADERS: List[str] = ["No", "Medicine", "Qty", "Rate", "Amount"]


def _clean_line(line: str) -> str:
    """
    Normalize a single line WITHOUT collapsing multi-space runs.

    Unlike the other formatters, this module relies on runs of 2+
    spaces as the column-boundary signal (see `_split_columns`), so
    internal whitespace must be preserved. Only tabs are normalized to
    spaces and leading/trailing whitespace is trimmed.
    """
    return line.replace("\t", "  ").strip()


def _split_columns(line: str) -> List[str]:
    """Split a line into column tokens using 2+ spaces as a separator."""
    return [part.strip() for part in re.split(r"\s{2,}", line.strip()) if part.strip()]


def _map_trailing_numbers(numbers: List[str]) -> Tuple[str, str, str]:
    """
    Map a list of trailing numeric column values to (qty, rate, amount)
    based purely on count/position, per the rules in the module
    docstring.

    Args:
        numbers: Trailing numeric tokens found after the item label,
            in their original left-to-right order.

    Returns:
        (qty, rate, amount) tuple as strings.
    """
    if len(numbers) == 3:
        qty, rate, amount = numbers
    elif len(numbers) == 4:
        qty, _ignored, rate, amount = numbers
    else:  # 5 or more
        qty = numbers[0]
        amount = numbers[-1]
        rate = numbers[-2]

    return qty, rate, amount


def _parse_bill_line(line: str) -> Optional[Tuple[str, List[str]]]:
    """
    Attempt to parse a single line as "<label columns...> <numeric
    columns...>", where the trailing 3+ columns are numeric.

    Args:
        line: A single cleaned line.

    Returns:
        (label, trailing_numbers) tuple, or None if the line doesn't
        have at least 3 trailing numeric columns.
    """
    columns = _split_columns(line)
    if len(columns) < 4:  # need at least 1 label column + 3 numbers
        return None

    # Walk backwards collecting numeric trailing columns.
    trailing_numbers: List[str] = []
    idx = len(columns) - 1
    while idx >= 0 and _NUMERIC_COLUMN_RE.match(columns[idx]):
        trailing_numbers.insert(0, columns[idx])
        idx -= 1

    if len(trailing_numbers) < 3:
        return None

    label_columns = columns[: idx + 1]
    if not label_columns:
        return None

    # Drop a leading serial-number column (e.g. "1", "2") if the label
    # otherwise has real text content.
    if len(label_columns) > 1 and _SMALL_INT_RE.match(label_columns[0]):
        label_columns = label_columns[1:]

    label = " ".join(label_columns).strip()
    if not label:
        return None

    return label, trailing_numbers


def extract_bill_items(text: str) -> List[Tuple[str, str, str, str]]:
    """
    Scan cleaned OCR text and extract (particulars, qty, rate, amount)
    rows from a pharmacy bill.

    Args:
        text: Raw or lightly cleaned OCR text.

    Returns:
        List of (particulars, qty, rate, amount) tuples, in the order
        they were found.
    """
    raw_lines = [_clean_line(line) for line in text.splitlines()]
    lines = [line for line in raw_lines if line]

    rows: List[Tuple[str, str, str, str]] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # --- Strategy 1: single line "label ... numbers" ---
        parsed = _parse_bill_line(line)
        if parsed:
            label, numbers = parsed
            qty, rate, amount = _map_trailing_numbers(numbers)
            rows.append((label, qty, rate, amount))
            i += 1
            continue

        # --- Strategy 2: multi-line record: label line followed by
        # several standalone numeric lines (3+) before the next
        # non-numeric line. ---
        if re.search(r"[A-Za-z]", line) and not _NUMERIC_COLUMN_RE.match(line):
            lookahead_numbers: List[str] = []
            j = i + 1
            while j < n and _NUMERIC_COLUMN_RE.match(lines[j]) and len(lookahead_numbers) < 6:
                lookahead_numbers.append(lines[j])
                j += 1

            if len(lookahead_numbers) >= 3:
                qty, rate, amount = _map_trailing_numbers(lookahead_numbers)
                rows.append((line, qty, rate, amount))
                i = j
                continue

        i += 1

    return rows


def extract_header_info(text: str) -> Dict[str, str]:
    """
    Extract bill header information (patient, bill no, GSTIN, date,
    store, doctor, etc.) from any line matching the fully generic
    "label: value" shape. No fixed list of expected field names is
    required, so this generalizes to any pharmacy's bill layout.

    Args:
        text: Raw or lightly cleaned OCR text.

    Returns:
        Ordered dictionary-like mapping of detected field label to
        value (insertion order preserved, duplicate labels overwritten
        by their last occurrence).
    """
    header_info: Dict[str, str] = {}

    for raw_line in text.splitlines():
        line = _clean_line(raw_line)
        if not line or ":" not in line:
            continue

        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()

        # Require a plausible short field label (not a full sentence)
        # and a non-empty value to avoid false positives.
        if key and value and len(key.split()) <= 5:
            header_info[key] = value

    return header_info


def format_pharmacy_bill(text: str) -> str:
    """
    Format raw OCR text from a pharmacy bill into a readable string
    containing extracted header information followed by a tabulated
    list of billed items.

    Args:
        text: Raw (or cleaned) OCR text believed to be a pharmacy bill.

    Returns:
        Formatted string with a "Bill Details" section (if any
        key/value header fields were found) and an "Items" table (if
        any item rows were found). Falls back to the original text if
        neither could be detected.
    """
    header_info = extract_header_info(text)
    items = extract_bill_items(text)

    sections: List[str] = []

    if header_info:
        header_lines = [f"{key} : {value}" for key, value in header_info.items()]
        sections.append("Bill Details\n" + "\n".join(header_lines))

    if items:
        numbered_rows = [
            (index + 1, medicine, qty, rate, amount)
            for index, (medicine, qty, rate, amount) in enumerate(items)
        ]
        table = tabulate(numbered_rows, headers=_TABLE_HEADERS, tablefmt="grid")
        sections.append("Items\n" + table)

    if not sections:
        return (
            "No bill details or item rows could be automatically detected.\n\n"
            "Original OCR text:\n" + text.strip()
        )

    return "\n\n".join(sections)