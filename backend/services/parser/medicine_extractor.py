"""
medicine_extractor.py

Medicine extraction module for a prescription analysis pipeline.

Handles two input shapes automatically:
  1. Block format - blank-line-separated blocks, first line = name
  2. Table format - pipe-delimited rows with dynamic headers

Public API:
    extract_medicines(text: str) -> dict
"""

import logging
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

try:
    from .regex_patterns import MEDICINE_LINE_PATTERN
    from .utilsy import (
        classify_line,
        is_table_format,
        normalize_dosage,
        normalize_name,
        normalize_timing,
        normalize_timing_fuzzy,
        normalize_unit,
        parse_table_generic,
        split_into_blocks,
        strip_form_prefix,
    )
except ImportError:
    from regex_patterns import MEDICINE_LINE_PATTERN
    from utilsy import (
        classify_line,
        is_table_format,
        normalize_dosage,
        normalize_name,
        normalize_timing,
        normalize_timing_fuzzy,
        normalize_unit,
        parse_table_generic,
        split_into_blocks,
        strip_form_prefix,
    )

logger = logging.getLogger(__name__)


@dataclass
class Medicine:
    name: str
    dosage: Optional[str] = None
    unit: Optional[str] = None
    schedule: Optional[str] = None
    timing: Optional[str] = None
    form: Optional[str] = None
    duration: Optional[str] = None
    frequency: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return asdict(self)


HEADER_ALIASES = {
    "medicine": "name",
    "medicine_name": "name",
    "drug": "name",
    "drug_name": "name",
    "name": "name",
    "dosage": "_dosage_or_timing",
    "dose": "_dosage_or_timing",
    "timing": "timing",
    "time": "timing",
    "schedule": "schedule",
    "frequency": "frequency",
    "duration": "duration",
    "days": "duration",
    "form": "form",
    "unit": "unit",
}


def extract_medicines(text: str) -> dict:
    """Public entry point. Auto-detects table vs block format."""
    try:
        if is_table_format(text):
            return _extract_table(text)
        return _extract_blocks(text)
    except Exception:
        logger.exception("Unexpected error during medicine extraction")
        return {"medicines": []}


def extract_table_key_values(text: str) -> dict:
    """
    Return pure dynamic JSON-style rows exactly from table headers.

    Use this when you want:
      {"medicine": "...", "dosage": "...", "duration": "..."}
    instead of normalized medicine fields.
    """
    return {"rows": parse_table_generic(text)}


def _extract_table(text: str) -> dict:
    rows = parse_table_generic(text)
    medicines: List[dict] = []

    for row in rows:
        med = Medicine(name="")
        extras: Dict[str, object] = {}

        for header, value in row.items():
            if not value:
                continue
            if header.endswith("_raw") or header == "_extra_columns":
                extras[header] = value
                continue

            canonical = HEADER_ALIASES.get(header, header)

            if canonical == "name":
                med.name = normalize_name(strip_form_prefix(str(value)))
            elif canonical == "_dosage_or_timing":
                timing_guess = normalize_timing_fuzzy(str(value))
                if timing_guess:
                    med.timing = timing_guess
                    med.dosage = str(value).strip()
                else:
                    med.dosage = str(value).strip()
            elif canonical == "duration":
                med.duration = str(value).strip()
            elif canonical == "schedule":
                med.schedule = str(value).strip()
            elif canonical == "frequency":
                med.frequency = str(value).strip()
            elif canonical == "form":
                med.form = str(value).strip()
            elif canonical == "unit":
                med.unit = str(value).strip()
            elif canonical == "timing":
                med.timing = normalize_timing_fuzzy(str(value)) or str(value).strip()
            else:
                extras[header] = value

        if not med.name:
            continue

        med_dict = med.to_dict()
        med_dict.update(extras)
        medicines.append(med_dict)
        logger.debug("Extracted medicine from table: %s", med_dict)

    return {"medicines": medicines}


def _extract_blocks(text: str) -> dict:
    blocks = split_into_blocks(text)
    medicines: List[Medicine] = []

    for block in blocks:
        if not block:
            continue

        med = _parse_name_line(block[0])
        if med is None:
            continue

        for line in block[1:]:
            kind = classify_line(line)
            if kind == "schedule":
                med.schedule = line.strip()
            elif kind == "timing":
                med.timing = normalize_timing(line)
            elif kind == "form":
                med.form = line.strip()
            elif kind == "duration":
                med.duration = line.strip()
            elif kind == "frequency":
                med.frequency = line.strip()

        medicines.append(med)
        logger.debug("Extracted medicine from block: %s", med)

    return {"medicines": [medicine.to_dict() for medicine in medicines]}


def _parse_name_line(line: str) -> Optional[Medicine]:
    match = MEDICINE_LINE_PATTERN.match(line)
    if match:
        return Medicine(
            name=normalize_name(match.group("name")),
            dosage=normalize_dosage(match.group("dosage")),
            unit=normalize_unit(match.group("unit")),
        )

    cleaned_name = line.strip()
    if not cleaned_name:
        return None
    return Medicine(name=normalize_name(cleaned_name))
