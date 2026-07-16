"""
aliases.py
----------

Central store for lab-test name aliases.

OCR output frequently abbreviates test names (e.g. "Hb" instead of
"Hemoglobin"). This module maps every known alias to a single,
standardized test name so downstream consumers (Gemini, UI, etc.)
always see consistent naming.

To add a new alias, just add a new key/value pair to ALIAS_MAP.
Keys are matched case-insensitively by `normalize_test_name`.
"""

from typing import Dict

# Maps: OCR alias (as it might appear in a report) -> standardized name
ALIAS_MAP: Dict[str, str] = {
    "Hb": "Hemoglobin",
    "HB": "Hemoglobin",
    "HGB": "Hemoglobin",
    "Hgb": "Hemoglobin",
    "PLT": "Platelets",
    "Plt": "Platelets",
    "PLATELET": "Platelets",
    "PLATELETS": "Platelets",
    "GLU": "Glucose",
    "Glu": "Glucose",
    "FBS": "Glucose",
    "CREA": "Creatinine",
    "Crea": "Creatinine",
    "CREAT": "Creatinine",
    "TLC": "WBC",
    "Tlc": "WBC",
    "WBC": "WBC",
    "RBC": "RBC",
    "HCT": "Hematocrit",
    "PCV": "Hematocrit",
}


def normalize_test_name(raw_name: str) -> str:
    """
    Normalize a raw OCR test name into its standardized form.

    Performs a case-insensitive lookup against ALIAS_MAP. If no alias
    is found, the cleaned original name is returned unchanged so that
    tests not present in the alias table are not silently dropped.

    Args:
        raw_name: The test name as it appeared in the OCR text.

    Returns:
        The standardized test name, or the cleaned original if no
        alias mapping exists.
    """
    cleaned = raw_name.strip()

    for alias, standard in ALIAS_MAP.items():
        if cleaned.lower() == alias.lower():
            return standard

    return cleaned
