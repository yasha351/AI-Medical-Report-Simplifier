"""
test_parser.py
--------------

Unit tests for the Lab Report Parser module.

Run with:
    python -m pytest test_parser.py -v
or:
    python -m unittest test_parser.py -v
"""

import unittest

from parser import parse_lab_report


class TestParseLabReport(unittest.TestCase):
    """Tests for parse_lab_report()."""

    def test_basic_report(self):
        text = (
            "Hemoglobin      10.2 g/dL\n"
            "WBC             6200 /uL\n"
            "Platelets       250000 /uL\n"
            "Glucose         98 mg/dL\n"
            "Creatinine      1.1 mg/dL\n"
        )
        result = parse_lab_report(text)

        names = [t["name"] for t in result["tests"]]
        self.assertIn("Hemoglobin", names)
        self.assertIn("WBC", names)
        self.assertIn("Platelets", names)
        self.assertIn("Glucose", names)
        self.assertIn("Creatinine", names)
        self.assertEqual(len(result["tests"]), 5)

    def test_alias_normalization(self):
        text = (
            "Hb    10.2 g/dL\n"
            "HGB   10.5 g/dL\n"
            "PLT   250000 /uL\n"
            "GLU   98 mg/dL\n"
            "CREA  1.1 mg/dL\n"
            "TLC   6200 /uL\n"
        )
        result = parse_lab_report(text)
        names = [t["name"] for t in result["tests"]]

        self.assertEqual(names.count("Hemoglobin"), 2)  # Hb + HGB
        self.assertIn("Platelets", names)
        self.assertIn("Glucose", names)
        self.assertIn("Creatinine", names)
        self.assertIn("WBC", names)  # from TLC

    def test_numeric_and_unit_extraction(self):
        text = "Glucose 98 mg/dL"
        result = parse_lab_report(text)
        test = result["tests"][0]

        self.assertEqual(test["name"], "Glucose")
        self.assertEqual(test["value"], 98)
        self.assertEqual(test["unit"], "mg/dL")

    def test_float_value(self):
        text = "Creatinine 1.1 mg/dL"
        result = parse_lab_report(text)
        test = result["tests"][0]

        self.assertIsInstance(test["value"], float)
        self.assertEqual(test["value"], 1.1)

    def test_patient_info_extraction(self):
        text = (
            "Patient Name: Jane Smith\n"
            "Age: 34\n"
            "Gender: Female\n"
            "Hemoglobin 12.5 g/dL\n"
        )
        result = parse_lab_report(text)

        self.assertEqual(result["patient"]["name"], "Jane Smith")
        self.assertEqual(result["patient"]["age"], "34")
        self.assertEqual(result["patient"]["gender"], "Female")

    def test_ignores_hospital_and_reference_range(self):
        text = (
            "Hospital: City Care Hospital\n"
            "Doctor: Dr. Rao\n"
            "Reference Range: 12-16 g/dL\n"
            "Hemoglobin 10.2 g/dL\n"
        )
        result = parse_lab_report(text)

        # Only the real test line should be picked up.
        self.assertEqual(len(result["tests"]), 1)
        self.assertEqual(result["tests"][0]["name"], "Hemoglobin")

    def test_malformed_lines_are_skipped_gracefully(self):
        text = (
            "This is just some random OCR noise !!\n"
            "Hemoglobin\n"                # missing value entirely
            "Glucose -- mg/dL\n"          # non-numeric value
            "WBC 6200 /uL\n"              # valid line
        )
        result = parse_lab_report(text)

        names = [t["name"] for t in result["tests"]]
        self.assertEqual(names, ["WBC"])

    def test_ignores_trailing_reference_range_on_same_line(self):
        # Realistic OCR output where the reference range is tabbed
        # onto the same line as the result -- only the result itself
        # should be captured, not the range.
        text = "Hemoglobin        10.2       g/dL       13.0 - 17.0\n"
        result = parse_lab_report(text)

        self.assertEqual(len(result["tests"]), 1)
        test = result["tests"][0]
        self.assertEqual(test["name"], "Hemoglobin")
        self.assertEqual(test["value"], 10.2)
        self.assertEqual(test["unit"], "g/dL")

    def test_empty_input(self):
        result = parse_lab_report("")
        self.assertEqual(result["tests"], [])
        self.assertEqual(result["patient"]["name"], "")

    def test_no_medical_interpretation_fields_present(self):
        text = "Glucose 98 mg/dL"
        result = parse_lab_report(text)
        test = result["tests"][0]

        # Only name/value/unit should be present -- no diagnosis,
        # no normal-range flags, no interpretation of any kind.
        self.assertEqual(set(test.keys()), {"name", "value", "unit"})


if __name__ == "__main__":
    unittest.main()
