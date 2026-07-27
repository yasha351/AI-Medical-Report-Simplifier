"""
utilsy.py

Generic text-handling helpers for prescription parsing.
Includes fuzzy matching to tolerate OCR typos in time-of-day words,
and a generic pipe-table parser that reads whatever headers are
actually present instead of assuming fixed column names.
"""

import difflib
import logging
import re
from typing import Dict, List, Optional

try:
    from .regex_patterns import (
        DOSAGE_FORM_PREFIXES,
        DURATION_LINE_PATTERN,
        FORM_LINE_PATTERN,
        FREQUENCY_LINE_PATTERN,
        NUMERIC_SCHEDULE_PATTERN,
        TABLE_SEPARATOR_LINE,
        TIME_ABBREVIATIONS,
        TIME_WORDS,
        TIMING_LINE_PATTERN,
    )
except ImportError:
    from regex_patterns import (
        DOSAGE_FORM_PREFIXES,
        DURATION_LINE_PATTERN,
        FORM_LINE_PATTERN,
        FREQUENCY_LINE_PATTERN,
        NUMERIC_SCHEDULE_PATTERN,
        TABLE_SEPARATOR_LINE,
        TIME_ABBREVIATIONS,
        TIME_WORDS,
        TIMING_LINE_PATTERN,
    )

logger = logging.getLogger(__name__)


OCR_VALUE_REPLACEMENTS = {
    "motning": "Morning",
    "moming": "Morning",
    "momung": "Morning",
    "momlng": "Morning",
    "mornlng": "Morning",
    "aft": "Afternoon",
    "at": "Afternoon",
    "eve": "Evening",
}


def split_into_blocks(text: str) -> List[List[str]]:
    """Split raw text into blocks separated by blank lines."""
    if not text:
        return []
    raw_blocks = re.split(r"\n\s*\n", text.strip())
    blocks = []
    for raw_block in raw_blocks:
        lines = [line.strip() for line in raw_block.splitlines()]
        lines = [line for line in lines if line]
        if lines:
            blocks.append(lines)
    return blocks


def classify_line(line: str) -> str:
    if NUMERIC_SCHEDULE_PATTERN.match(line):
        return "schedule"
    if DURATION_LINE_PATTERN.search(line):
        return "duration"
    if TIMING_LINE_PATTERN.search(line):
        return "timing"
    if FORM_LINE_PATTERN.match(line):
        return "form"
    if FREQUENCY_LINE_PATTERN.search(line):
        return "frequency"
    return "unknown"


def normalize_timing(line: str) -> str:
    """Exact-match timing extraction for clean block input."""
    found = re.findall(r"morning|afternoon|evening|night", line, re.IGNORECASE)
    seen = []
    for word in found:
        cap = word.capitalize()
        if cap not in seen:
            seen.append(cap)
    return ", ".join(seen)


def fuzzy_match_time_word(token: str) -> Optional[str]:
    """Match one OCR-garbled token against known time-of-day words."""
    token_clean = re.sub(r"[^a-zA-Z]", "", token).lower()
    if not token_clean:
        return None
    if token_clean in TIME_ABBREVIATIONS:
        return TIME_ABBREVIATIONS[token_clean]
    matches = difflib.get_close_matches(token_clean, TIME_WORDS, n=1, cutoff=0.6)
    return matches[0] if matches else None


def normalize_timing_fuzzy(text: str) -> str:
    """
    Extract time-of-day words from OCR text tolerant of typos.
    Example: '1 Motning, 1 Night.' -> 'Morning, Night'
    """
    tokens = re.split(r"[,\s/]+", text)
    seen = []
    for token in tokens:
        canonical = fuzzy_match_time_word(token)
        if canonical:
            cap = canonical.capitalize()
            if cap not in seen:
                seen.append(cap)
    return ", ".join(seen)


def normalize_name(name: str) -> str:
    words = name.strip().split()
    return " ".join(word.capitalize() for word in words)


def normalize_unit(unit: str) -> str:
    return unit.strip().lower()


def normalize_dosage(dosage: str) -> str:
    return dosage.strip()


def strip_form_prefix(name: str) -> str:
    """Remove 'TAB.' or 'CAP.' style prefixes from a medicine name."""
    cleaned = name.strip()
    for prefix in DOSAGE_FORM_PREFIXES:
        pattern = re.compile(r"^" + re.escape(prefix) + r"\.?\s+", re.IGNORECASE)
        if pattern.match(cleaned):
            cleaned = pattern.sub("", cleaned)
            break
    return cleaned


def is_table_format(text: str) -> bool:
    """Detect pipe-delimited table OCR output."""
    return len(_real_pipe_lines(text)) >= 2


def clean_header(raw_header: str) -> str:
    """Convert 'Medicine Name' to 'medicine_name'."""
    cleaned = raw_header.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")
    return cleaned or "column"


def make_unique_headers(headers: List[str]) -> List[str]:
    """Avoid overwriting values when duplicate/blank headers appear."""
    counts: Dict[str, int] = {}
    unique = []
    for header in headers:
        count = counts.get(header, 0) + 1
        counts[header] = count
        unique.append(header if count == 1 else f"{header}_{count}")
    return unique


def clean_table_value(value: str) -> str:
    """Best-effort OCR cleanup after structural parsing is already done."""
    cleaned = value.strip()
    for typo, replacement in OCR_VALUE_REPLACEMENTS.items():
        cleaned = re.sub(rf"\b{re.escape(typo)}\b", replacement, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bI\b(?=\s+(Morning|Afternoon|Evening|Night)\b)", "1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _real_pipe_lines(text: str) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return [line for line in lines if "|" in line and not TABLE_SEPARATOR_LINE.fullmatch(line)]


def parse_table_generic(text: str, include_raw: bool = True) -> List[Dict[str, str]]:
    """
    Parse a pipe-delimited table with unknown headers.

    The first real pipe row becomes the keys. Every following pipe row
    becomes values connected to those keys by matching column position.
    """
    pipe_lines = _real_pipe_lines(text)
    if not pipe_lines:
        return []

    raw_headers = [cell.strip() for cell in pipe_lines[0].strip("|").split("|")]
    headers = make_unique_headers([clean_header(header) for header in raw_headers])

    rows: List[Dict[str, str]] = []
    for line in pipe_lines[1:]:
        values = [cell.strip() for cell in line.strip("|").split("|")]
        row: Dict[str, str] = {}

        for index, header in enumerate(headers):
            raw_value = values[index] if index < len(values) else ""
            cleaned_value = clean_table_value(raw_value)
            row[header] = cleaned_value
            if include_raw and raw_value.strip() and cleaned_value != raw_value.strip():
                row[f"{header}_raw"] = raw_value.strip()

        if len(values) > len(headers):
            row["_extra_columns"] = [clean_table_value(value) for value in values[len(headers) :]]

        rows.append(row)

    return rows
