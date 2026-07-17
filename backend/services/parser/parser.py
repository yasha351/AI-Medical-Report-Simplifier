"""
parser.py
---------

The Lab Report Parser module.

Public entry point: `parse_lab_report(text: str) -> dict`

This module converts raw OCR text extracted from a laboratory report
into structured JSON (returned here as a Python dict). It performs
NO medical interpretation, diagnosis, or normal-range comparison —
those responsibilities belong to the downstream Gemini API step.

Pipeline:
    OCR Text
      -> split into lines
      -> clean text
      -> ignore empty / irrelevant lines
      -> identify test name
      -> extract numeric value
      -> extract unit
      -> normalize alias
      -> build JSON
      -> return JSON
"""

from typing import Optional

from aliases import normalize_test_name
from models import LabTest, Patient, Report
from utils import (
    clean_text,
    extract_patient_field,
    extract_test_from_line,
    is_ignorable_line,
    is_patient_info_line,
    split_lines,
)


def parse_lab_report(text: str) -> dict:
    """
    Parse raw OCR text from a lab report into structured JSON.

    Args:
        text: Raw OCR output as a single string. May contain patient
            metadata (name, age, gender), hospital/doctor info,
            reference ranges, and comments in addition to test
            results. Malformed or unrelated lines are skipped
            gracefully rather than raising an exception.

    Returns:
        A dictionary of the form:
        {
            "patient": {"name": str, "age": str, "gender": str},
            "tests": [{"name": str, "value": number, "unit": str}, ...]
        }
    """
    report = Report(patient=Patient(), tests=[])

    if not text or not text.strip():
        return report.to_dict()

    cleaned = clean_text(text)
    lines = split_lines(cleaned)

    for line in lines:
        # 1. Patient metadata (name / age / gender)
        if is_patient_info_line(line):
            _apply_patient_field(report.patient, line)
            continue

        # 2. Non-test metadata: hospital, doctor, address, reference
        #    ranges, comments, etc. -- ignored entirely.
        if is_ignorable_line(line):
            continue

        # 3. Attempt to extract a lab test result from the line.
        lab_test = extract_test_from_line(line)
        if lab_test is None:
            # Malformed / unrelated line -- skip gracefully.
            continue

        lab_test.name = normalize_test_name(lab_test.name)
        report.tests.append(lab_test)

    return report.to_dict()


def _apply_patient_field(patient: Patient, line: str) -> None:
    """
    Extract a patient field (name/age/gender) from a line and apply
    it to the given Patient object in place, if found.
    """
    field_and_value = extract_patient_field(line)
    if field_and_value is None:
        return

    field_name, value = field_and_value
    if field_name == "name" and not patient.name:
        patient.name = value
    elif field_name == "age" and not patient.age:
        patient.age = value
    elif field_name == "gender" and not patient.gender:
        patient.gender = value


if __name__ == "__main__":
    import json

    sample = """
    Hospital: City Care Hospital
    Patient Name: John Doe
    Age: 45
    Gender: Male

    Hemoglobin      10.2 g/dL
    WBC             6200 /uL
    Platelets       250000 /uL
    Glucose         98 mg/dL
    Creatinine      1.1 mg/dL
    Hb              10.5 g/dL
    """

    result = parse_lab_report(sample)
    print(json.dumps(result, indent=2))
