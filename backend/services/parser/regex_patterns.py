"""
regex_patterns.py

Centralized regex patterns for prescription parsing.
Supports two OCR shapes:
  1. Block format - "Name Dosage Unit" line + free-form detail lines
  2. Table format - pipe-delimited rows with dynamic headers
"""

import re

DOSAGE_FORM_PREFIXES = ("TABLET", "TAB", "CAPSULE", "CAP", "INJECTION", "INJ", "SYRUP")
DOSAGE_UNITS = ("mg", "mcg", "ml", "g", "iu")
DURATION_UNITS = ("day", "week", "month")
FREQUENCY_WORDS = ("daily", "weekly", "monthly", "once", "twice", "thrice", "alternate")

TIME_WORDS = ("morning", "afternoon", "evening", "night")
TIME_ABBREVIATIONS = {"aft": "afternoon", "eve": "evening", "at": "afternoon"}

MEDICINE_LINE_PATTERN = re.compile(
    r"^\s*(?:(?P<prefix>" + "|".join(DOSAGE_FORM_PREFIXES) + r")\.?\s+)?"
    r"(?P<name>[A-Za-z][A-Za-z\-]*(?:\s+[A-Za-z0-9\-]+)*?)\s+"
    r"(?P<dosage>\d+(?:\.\d+)?)\s*(?P<unit>" + "|".join(DOSAGE_UNITS) + r")\b",
    re.IGNORECASE,
)

NUMERIC_SCHEDULE_PATTERN = re.compile(r"^\s*(?:\d+-\d+-\d+|SOS)\s*$", re.IGNORECASE)
TIMING_LINE_PATTERN = re.compile(r"(?:" + "|".join(TIME_WORDS) + r")", re.IGNORECASE)

FORM_WORDS = ("tablet", "tab", "capsule", "cap", "drop", "spoon", "ml", "puff")
FORM_LINE_PATTERN = re.compile(
    r"^\s*(?P<qty>\d+(?:/\d+)?)\s*(?P<form>" + "|".join(FORM_WORDS) + r")s?\b",
    re.IGNORECASE,
)

DURATION_LINE_PATTERN = re.compile(
    r"(?P<amount>\d+)\s*(?P<unit>" + "|".join(DURATION_UNITS) + r")s?\b",
    re.IGNORECASE,
)

FREQUENCY_LINE_PATTERN = re.compile(r"(?:" + "|".join(FREQUENCY_WORDS) + r")", re.IGNORECASE)

# Separator rows are visual decoration only, for example:
# -----+------+-----
# -----|------|-----
TABLE_SEPARATOR_LINE = re.compile(r"^[\s\-+|:]+$")
