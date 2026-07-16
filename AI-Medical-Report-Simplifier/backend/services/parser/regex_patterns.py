"""
regex_patterns.py

Centralized regex patterns used by the Medicine Extraction Module.
Keeping all patterns here makes it easy to extend support for new
prescription formats without touching parsing logic.
"""

import re

# Prefixes that indicate a dosage form and should be stripped from
# the final medicine name.
DOSAGE_FORM_PREFIXES = (
    "TABLET",
    "TAB",
    "CAPSULE",
    "CAP",
    "INJECTION",
    "INJ",
    "SYRUP",
)

# Recognized dosage units (always normalized to lowercase in output).
DOSAGE_UNITS = ("mg", "mcg", "ml", "g")

# Matches an optional dosage-form prefix, followed by a medicine name
# (one or more words), followed by a dosage number and unit.
#
# Examples matched:
#   "TAB PARACETAMOL 650 MG"
#   "CAP AMOXICILLIN 500 MG"
#   "AZITHROMYCIN 250 MG"
MEDICINE_LINE_PATTERN = re.compile(
    r"^\s*"
    r"(?:(?P<prefix>" + "|".join(DOSAGE_FORM_PREFIXES) + r")\s+)?"
    r"(?P<name>[A-Za-z][A-Za-z\-]*(?:\s+[A-Za-z][A-Za-z\-]*)*?)\s+"
    r"(?P<dosage>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>" + "|".join(DOSAGE_UNITS) + r")\b",
    re.IGNORECASE,
)

# Matches a schedule line, e.g. "1-0-1", "0-1-0", or "SOS".
SCHEDULE_PATTERN = re.compile(
    r"^\s*(?:\d+-\d+-\d+|SOS)\s*$",
    re.IGNORECASE,
)
