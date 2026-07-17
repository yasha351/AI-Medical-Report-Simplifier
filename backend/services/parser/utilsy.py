"""
utilsy.py

Generic text-handling helpers for prescription parsing.
No medicine-specific logic lives here — only reusable helpers.
"""

import re
import logging
from typing import List

from .regex_patterns import (
    NUMERIC_SCHEDULE_PATTERN,
    DURATION_LINE_PATTERN,
    TIMING_LINE_PATTERN,
    FORM_LINE_PATTERN,
    FREQUENCY_LINE_PATTERN,
)

logger = logging.getLogger(__name__)


def split_into_blocks(text: str) -> List[List[str]]:
    """
    Split raw text into blocks separated by blank lines.
    Each block is a list of its non-empty, stripped lines.
    The FIRST line of each block is assumed to be the medicine name line.
    """
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
    """
    Classify a non-name line as one of:
    schedule, duration, timing, form, frequency, unknown.
    Order = priority; checked top to bottom, first match wins.
    """
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
    """
    Extract only time-of-day words from a line, ignoring numbers,
    bullets, commas, and notes like '(Before Food)'.
    '1 Morning, 1 Night (Before Food)' -> 'Morning, Night'
    """
    found = re.findall(r"morning|afternoon|evening|night", line, re.IGNORECASE)
    seen = []
    for word in found:
        cap = word.capitalize()
        if cap not in seen:
            seen.append(cap)
    return ", ".join(seen)


def normalize_name(name: str) -> str:
    """Title-case a medicine name, collapsing extra whitespace."""
    words = name.strip().split()
    return " ".join(word.capitalize() for word in words)


def normalize_unit(unit: str) -> str:
    return unit.strip().lower()


def normalize_dosage(dosage: str) -> str:
    return dosage.strip()