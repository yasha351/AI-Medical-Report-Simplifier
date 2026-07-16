"""
utils.py

Generic text-handling helpers for the Medicine Extraction Module.
These functions are intentionally free of any medicine-specific
business logic so they can be reused or tested independently.
"""

import logging
from typing import List

from .regex_patterns import SCHEDULE_PATTERN

logger = logging.getLogger(__name__)


def split_lines(text: str) -> List[str]:
    """
    Split raw text into a list of non-empty, stripped lines.

    Args:
        text: Raw cleaned prescription text.

    Returns:
        List of non-empty stripped lines, preserving order.
    """
    if not text:
        return []

    lines = text.splitlines()
    cleaned = [line.strip() for line in lines]
    non_empty = [line for line in cleaned if line]

    logger.debug("split_lines: %d non-empty lines found", len(non_empty))
    return non_empty


def is_schedule_line(line: str) -> bool:
    """
    Check whether a given line represents a dosage schedule.

    Args:
        line: A single line of text.

    Returns:
        True if the line matches a schedule pattern (e.g. "1-0-1", "SOS").
    """
    return bool(SCHEDULE_PATTERN.match(line))


def normalize_name(name: str) -> str:
    """
    Normalize a medicine name to title case with single spaces.

    Args:
        name: Raw extracted medicine name.

    Returns:
        Title-cased, whitespace-normalized medicine name.
    """
    words = name.strip().split()
    return " ".join(word.capitalize() for word in words)


def normalize_unit(unit: str) -> str:
    """
    Normalize a dosage unit to lowercase.

    Args:
        unit: Raw extracted unit string.

    Returns:
        Lowercase unit string.
    """
    return unit.strip().lower()


def normalize_dosage(dosage: str) -> str:
    """
    Normalize a dosage value string (strips whitespace, no unit attached).

    Args:
        dosage: Raw extracted dosage numeral.

    Returns:
        Cleaned dosage string.
    """
    return dosage.strip()
