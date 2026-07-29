import json

from backend.services.ocr.ocr_service import extract_text
from backend.services.parser.parser import parse_lab_report


def process_lab_report(file_path):
    # Step 1: OCR
    raw_text = extract_text(file_path)

    print("\n===== OCR OUTPUT =====\n")
    print(raw_text)

    # Step 2: Parse
    report = parse_lab_report(raw_text)

    # Step 3: Save JSON
    with open("lab_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print("\n===== JSON OUTPUT =====")
    print(json.dumps(report, indent=4))

    return report


if __name__ == "__main__":
    process_lab_report("backend/services/ocr/sample_reports/sample_report.pdf")