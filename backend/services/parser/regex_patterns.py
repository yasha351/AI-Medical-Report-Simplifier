"""
regex_patterns.py

Centralized regex patterns for prescription parsing.
Add new prefixes/units/time-words/frequency-words here — no need to
touch parsing logic in medicine_extractor.py or utils.py.
"""

import re

DOSAGE_FORM_PREFIXES = ("TABLET", "TAB", "CAPSULE", "CAP", "INJECTION", "INJ", "SYRUP")
DOSAGE_UNITS = ("mg", "mcg", "ml", "g", "iu")
TIME_WORDS = ("morning", "afternoon", "evening", "night")
FORM_WORDS = ("tablet", "tab", "capsule", "cap", "drop", "spoon", "ml", "puff")
DURATION_UNITS = ("day", "week", "month")
FREQUENCY_WORDS = ("daily", "weekly", "monthly", "once", "twice", "thrice", "alternate")

# Medicine name + dosage line. Prefix (TAB/CAP) is OPTIONAL.
# Matches: "TAB PARACETAMOL 650 MG", "Amoxicillin 500 mg", "Vitamin D3 60000 IU"
MEDICINE_LINE_PATTERN = re.compile(
    r"^\s*(?:(?P<prefix>" + "|".join(DOSAGE_FORM_PREFIXES) + r")\.?\s+)?"
    r"(?P<name>[A-Za-z][A-Za-z\-]*(?:\s+[A-Za-z0-9\-]+)*?)\s+"
    r"(?P<dosage>\d+(?:\.\d+)?)\s*(?P<unit>" + "|".join(DOSAGE_UNITS) + r")\b",
    re.IGNORECASE,
)

# Numeric schedule: "1-0-1", "SOS"
NUMERIC_SCHEDULE_PATTERN = re.compile(r"^\s*(?:\d+-\d+-\d+|SOS)\s*$", re.IGNORECASE)

# Word-based timing: "Morning • Afternoon • Night", "1 Morning, 1 Night"
TIMING_LINE_PATTERN = re.compile(r"(?:" + "|".join(TIME_WORDS) + r")", re.IGNORECASE)

# Form/quantity line: "1 tablet", "2 capsules"
FORM_LINE_PATTERN = re.compile(
    r"^\s*(?P<qty>\d+(?:/\d+)?)\s*(?P<form>" + "|".join(FORM_WORDS) + r")s?\b",
    re.IGNORECASE,
)

# Duration line: "5 days", "10 Days (Tot:20 Tab)"
DURATION_LINE_PATTERN = re.compile(
    r"(?P<amount>\d+)\s*(?P<unit>" + "|".join(DURATION_UNITS) + r")s?\b",
    re.IGNORECASE,
)

# Frequency phrasing that isn't a numeric schedule: "Once weekly", "Twice daily"
FREQUENCY_LINE_PATTERN = re.compile(
    r"(?:" + "|".join(FREQUENCY_WORDS) + r")", re.IGNORECASE
)