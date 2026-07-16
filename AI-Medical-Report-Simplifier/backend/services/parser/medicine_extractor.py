"""
medicine_extractor.py

Medicine Extraction Module for the Prescription Analysis pipeline.

Responsibility: convert cleaned prescription text into structured
medicine data. This module performs NO OCR, NO LLM calls, and NO
medical explanation/validation — extraction only.

Public API:
    extract_medicines(text: str) -> dict
"""

import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from .regex_patterns import MEDICINE_LINE_PATTERN
from .utils import (
    split_lines,
    is_schedule_line,
    normalize_name,
    normalize_unit,
    normalize_dosage,
)

logger = logging.getLogger(__name__)


@dataclass
class Medicine:
    """Structured representation of a single extracted medicine entry."""

    name: str
    dosage: str
    unit: str
    schedule: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Convert the Medicine instance to a plain dictionary."""
        return asdict(self)


def _parse_medicine_line(line: str) -> Optional[Medicine]:
    """
    Attempt to parse a single line as a medicine entry (name/dosage/unit).

    Args:
        line: A single stripped line of prescription text.

    Returns:
        A Medicine instance (schedule left empty) if the line matches,
        otherwise None.
    """
    match = MEDICINE_LINE_PATTERN.match(line)
    if not match:
        return None

    try:
        name = normalize_name(match.group("name"))
        dosage = normalize_dosage(match.group("dosage"))
        unit = normalize_unit(match.group("unit"))
    except (AttributeError, IndexError) as exc:
        # Should not happen given the pattern's named groups, but we
        # never want a malformed line to crash the pipeline.
        logger.warning("Failed to parse fields from line %r: %s", line, exc)
        return None

    if not name:
        return None

    return Medicine(name=name, dosage=dosage, unit=unit)


def _find_schedule(lines: List[str], start_index: int) -> Optional[str]:
    """
    Look ahead from a given index for a schedule line.

    Args:
        lines: Full list of non-empty lines.
        start_index: Index of the medicine line to look ahead from.

    Returns:
        The schedule string if the next line is a schedule, else None.
    """
    next_index = start_index + 1
    if next_index >= len(lines):
        return None

    if is_schedule_line(lines[next_index]):
        return lines[next_index].strip().upper() if lines[next_index].strip().upper() == "SOS" \
            else lines[next_index].strip()

    return None


def extract_medicines(text: str) -> dict:
    """
    Extract structured medicine data from cleaned prescription text.

    This is the only public function exposed by this module. It must
    never raise — on any failure it degrades gracefully to an empty
    medicines list.

    Args:
        text: Cleaned prescription text (output of the Text Cleaning
            module).

    Returns:
        A dictionary of the form:
            {"medicines": [{"name": ..., "dosage": ..., "unit": ...,
                             "schedule": ...}, ...]}
    """
    try:
        return _extract_medicines_impl(text)
    except Exception:
        # Extraction must never crash the pipeline.
        logger.exception("Unexpected error during medicine extraction")
        return {"medicines": []}


def _extract_medicines_impl(text: str) -> dict:
    """
    Core extraction logic, separated from the public function so that
    the error-handling boundary in extract_medicines() stays thin.

    Args:
        text: Cleaned prescription text.

    Returns:
        Dictionary with a "medicines" key mapping to a list of dicts.
    """
    medicines: List[Medicine] = []
    lines = split_lines(text)

    index = 0
    while index < len(lines):
        line = lines[index]

        medicine = _parse_medicine_line(line)
        if medicine is not None:
            schedule = _find_schedule(lines, index)
            if schedule is not None:
                medicine.schedule = schedule
                index += 1  # consume the schedule line too

            medicines.append(medicine)
            logger.debug("Extracted medicine: %s", medicine)

        index += 1

    return {"medicines": [m.to_dict() for m in medicines]}
