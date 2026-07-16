"""
models.py
---------

Lightweight data models representing the entities produced by the
lab report parser: Patient, LabTest, and the overall Report.

These are intentionally simple dataclasses with no external
dependencies, so this module stays independent of OCR and Gemini
implementations, per the project constraints.
"""

from dataclasses import dataclass, field
from typing import List, Union


@dataclass
class Patient:
    """Represents patient metadata extracted from a lab report."""

    name: str = ""
    age: str = ""
    gender: str = ""


@dataclass
class LabTest:
    """Represents a single laboratory test result."""

    name: str
    value: Union[int, float]
    unit: str


@dataclass
class Report:
    """Represents a fully parsed lab report: patient info + tests."""

    patient: Patient = field(default_factory=Patient)
    tests: List[LabTest] = field(default_factory=list)

    def to_dict(self) -> dict:
        """
        Convert the Report into a plain dictionary matching the
        structured JSON contract expected by downstream consumers
        (e.g. the Gemini explanation step).
        """
        return {
            "patient": {
                "name": self.patient.name,
                "age": self.patient.age,
                "gender": self.patient.gender,
            },
            "tests": [
                {"name": t.name, "value": t.value, "unit": t.unit}
                for t in self.tests
            ],
        }
