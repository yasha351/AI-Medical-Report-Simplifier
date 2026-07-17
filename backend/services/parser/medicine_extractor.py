"""
medicine_extractor.py

Medicine Extraction Module for the Prescription Analysis pipeline.

Responsibility: convert cleaned prescription text into structured
medicine data. NO OCR, NO LLM calls, NO medical explanation/validation
— extraction only.

STRUCTURE ASSUMPTION:
- Each medicine's info is one "block", separated from the next by a
  blank line.
- The FIRST line of each block is always the medicine name line
  (dosage/unit included on that line if OCR captured it).
- All other lines in the block are classified by their CONTENT
  (schedule / timing / form / duration / frequency), not their
  position — so line order within a block doesn't matter.

Public API:
    extract_medicines(text: str) -> dict
"""

import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from .regex_patterns import MEDICINE_LINE_PATTERN
from .utilsy import (
    split_into_blocks,
    classify_line,
    normalize_timing,
    normalize_name,
    normalize_unit,
    normalize_dosage,
)

logger = logging.getLogger(__name__)


@dataclass
class Medicine:
    """Structured representation of a single extracted medicine entry."""

    name: str
    dosage: Optional[str] = None
    unit: Optional[str] = None
    schedule: Optional[str] = None
    timing: Optional[str] = None
    form: Optional[str] = None
    duration: Optional[str] = None
    frequency: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


def extract_medicines(text: str) -> dict:
    """
    Extract structured medicine data from cleaned prescription text.

    This is the only public function exposed by this module. It must
    never raise — on any failure it degrades gracefully to an empty
    medicines list.

    Args:
        text: Cleaned prescription text (output of OCR / Text Cleaning
            module).

    Returns:
        {"medicines": [{"name": ..., "dosage": ..., "unit": ...,
                         "schedule": ..., "timing": ..., "form": ...,
                         "duration": ..., "frequency": ...}, ...]}
        Any field not found in the input is set to None.
    """
    try:
        return _extract(text)
    except Exception:
        logger.exception("Unexpected error during medicine extraction")
        return {"medicines": []}


def _extract(text: str) -> dict:
    blocks = split_into_blocks(text)
    medicines: List[Medicine] = []

    for block in blocks:
        if not block:
            continue

        name_line = block[0]
        med = _parse_name_line(name_line)
        if med is None:
            continue  # unusable first line, skip this block

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
            # "unknown" lines are ignored, never crash the pipeline

        medicines.append(med)
        logger.debug("Extracted medicine: %s", med)

    return {"medicines": [m.to_dict() for m in medicines]}


def _parse_name_line(line: str) -> Optional[Medicine]:
    """
    Parse the first line of a block as the medicine name line.
    Tries to also pull dosage+unit if present; falls back to
    name-only if no dosage number is found (handles OCR where the
    dosage is missing or misread).
    """
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


if __name__ == "__main__":
    import json

    sample_text = """
    TAB PARACETAMOL 650 MG
    1-0-1

    Amoxicillin 500 mg
    1 capsule
    Morning • Night
    7 days

    Cetirizine 10 mg

    DEMO MEDICINE 1
    1 Morning, 1 Night (Before Food)
    10 Days (Tot:20 Tab)

    Vitamin D3 60000 IU
    Once weekly

    Azithromycin 250 mg
    1 tablet
    Morning
    """

    result = extract_medicines(sample_text)
    print(json.dumps(result, indent=2))