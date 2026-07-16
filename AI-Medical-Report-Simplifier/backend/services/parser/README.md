# Lab Report Parser

A modular Python component that converts raw OCR text extracted from
laboratory reports into structured JSON. This module is one stage in
an AI-Powered Medical Report Simplifier pipeline:

```
User Uploads Lab Report
        │
        ▼
OCR (PaddleOCR)
        │
        ▼
Raw OCR Text
        │
        ▼
Lab Report Parser  ◄── this module
        │
        ▼
Structured JSON
        │
        ▼
Gemini API
        │
        ▼
Patient-Friendly Medical Explanation
```

This module **only parses OCR output**. It does not perform OCR,
medical diagnosis, disease prediction, normal-range comparison, or
any AI reasoning — those responsibilities belong to the Gemini step.

## Folder Structure

```
parser/
│── parser.py            # parse_lab_report(text) -> dict, main entry point
│── aliases.py            # alias -> standardized test name mapping
│── models.py              # Patient, LabTest, Report data models
│── utils.py               # text cleaning, regex matching, extraction helpers
│── test_parser.py         # unit tests
│── sample_reports/        # example OCR text files
│   │── sample1.txt
│   └── sample2_aliases.txt
└── README.md
```

## Usage

```python
from parser import parse_lab_report

ocr_text = """
Hemoglobin      10.2 g/dL
WBC             6200 /uL
Platelets       250000 /uL
Glucose         98 mg/dL
Creatinine      1.1 mg/dL
"""

report_json = parse_lab_report(ocr_text)
print(report_json)
```

Output:

```json
{
  "patient": {"name": "", "age": "", "gender": ""},
  "tests": [
    {"name": "Hemoglobin", "value": 10.2, "unit": "g/dL"},
    {"name": "WBC", "value": 6200, "unit": "/uL"},
    {"name": "Platelets", "value": 250000, "unit": "/uL"},
    {"name": "Glucose", "value": 98, "unit": "mg/dL"},
    {"name": "Creatinine", "value": 1.1, "unit": "mg/dL"}
  ]
}
```

## Integration with OCR and Gemini

This module has no dependency on any OCR library or the Gemini API.
A teammate wires it together like this:

```python
ocr_text = extract_text(file)             # OCR module
report_json = parse_lab_report(ocr_text)  # this module
gemini_response = explain_report(report_json)  # Gemini step
```

## Processing Pipeline

```
OCR Text
  → split into lines
  → clean text
  → ignore empty / irrelevant lines
  → identify test name
  → extract numeric value
  → extract unit
  → normalize alias
  → build JSON
  → return JSON
```

## Alias Handling

Aliases are stored in `aliases.py` in a single `ALIAS_MAP` dict so new
ones can be added without touching parsing logic:

```python
ALIAS_MAP = {
    "Hb": "Hemoglobin",
    "HGB": "Hemoglobin",
    "PLT": "Platelets",
    "GLU": "Glucose",
    "CREA": "Creatinine",
    "TLC": "WBC",
    ...
}
```

To add a new alias, just add a new key/value pair — no other code
changes are required.

## Ignored / Metadata Lines

Lines containing hospital name, doctor, address, reference ranges,
report dates, or comments are recognized and skipped automatically
(see `_IGNORABLE_KEYWORDS` in `utils.py`). Patient name/age/gender are
recognized separately and extracted into the `patient` block.

## Error Handling

The parser is designed to fail gracefully on malformed OCR text:

- Lines with no numeric value are skipped, not raised as errors.
- Empty or `None` input returns an empty report structure rather
  than raising an exception.
- Unrecognized test names are still included (unmapped names pass
  through `normalize_test_name` unchanged) so no data is silently
  dropped just because it's missing from the alias table.

## Running Tests

```bash
cd parser
python -m pytest test_parser.py -v
```

or, without pytest installed:

```bash
python -m unittest test_parser.py -v
```

## Extending

- **New aliases**: add to `ALIAS_MAP` in `aliases.py`.
- **New patient fields**: add a new regex pattern to
  `_PATIENT_FIELD_PATTERNS` in `utils.py`, and handle it in
  `_apply_patient_field()` in `parser.py`.
- **New ignorable metadata**: add a keyword to `_IGNORABLE_KEYWORDS`
  in `utils.py`.
