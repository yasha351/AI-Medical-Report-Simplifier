from services.parser.prescription_parser_service import process_prescription

IMAGE_PATH = "services/ocr/sample_reports/prescriptionnew.jpeg"

result = process_prescription(IMAGE_PATH)

print("\n========== FINAL JSON ==========\n")
print(result)