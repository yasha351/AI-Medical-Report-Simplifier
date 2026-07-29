<<<<<<< Updated upstream
<<<<<<< Updated upstream
from services.ocr.ocr_service import extract_text
def parse_lab_report(file_path):
=======
=======
>>>>>>> Stashed changes
from backend.services.ocr.ocr_service import extract_text
from backend.services.parser.parser import parse_lab_report
import json


def process_lab_report(file_path):
    """
    Complete pipeline:
    PDF/Image
        ↓
    OCR
        ↓
    Parser
        ↓
    JSON
    """

<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    raw_text = extract_text(file_path)

    report = parse_lab_report(raw_text)

    return report


if __name__ == "__main__":

    file_path = "sample_report.pdf"   # Change to your report path

    result = process_lab_report(file_path)

    with open("lab_report.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    print(json.dumps(result, indent=4))