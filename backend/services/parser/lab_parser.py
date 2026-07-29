from services.ocr.ocr_service import extract_text
def parse_lab_report(file_path):
    raw_text = extract_text(file_path)

    print("OCR TEXT:")
    print(raw_text)

    return {
        "report_type": "Lab Report",
        "raw_text": raw_text
    }