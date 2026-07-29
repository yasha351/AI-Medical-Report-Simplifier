import json

from services.ocr.ocr_service import extract_text
from services.parser.parser import parse_lab_report
from services.llm.gemini_service import summarize_report


def process_lab_report(file_path):
    # Step 1: OCR
    raw_text = extract_text(file_path)

    print("\n===== OCR OUTPUT =====\n")
    print(raw_text)

    # Step 2: Parse OCR text into structured JSON
    report = parse_lab_report(raw_text)

    print("\n===== PARSED JSON =====\n")
    print(json.dumps(report, indent=4))

    # Optional: Save parsed JSON for debugging
    with open("lab_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    # Step 3: Send parsed report to Gemini
    summary = summarize_report(report)

    print("\n===== GEMINI EXPLANATION =====\n")
    print(summary)

    # Return only the Gemini explanation
    return summary


if __name__ == "__main__":
    explanation = process_lab_report(
        "services/ocr/sample_reports/sample_report.pdf"
    )

    print("\n===== FINAL OUTPUT =====\n")
    print(explanation)