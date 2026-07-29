import logging

from services.ocr.ocr_service import extract_text
from services.ocr.formatters.prescription_formatter import format_prescription
from services.parser.medicine_extractor import extract_medicines
from services.llm.gemini_service import summarize_report

logger = logging.getLogger(__name__)


def process_prescription(file_path: str) -> dict:
    try:
        raw_text = extract_text(file_path)

        if not raw_text or not raw_text.strip():
            return {
                "parsed_data": {"medicines": []},
                "ai_summary": None,
            }

        formatted_table = format_prescription(raw_text)

        if formatted_table.startswith("No medicine rows could be automatically detected."):
            return {
                "parsed_data": {"medicines": []},
                "ai_summary": None,
            }

        parsed_data = extract_medicines(formatted_table)
        ai_summary = summarize_report(parsed_data)

        return {
            
            "ai_summary": ai_summary.strip(),
        }

    except Exception as e:
        logger.exception(e)
        return {
    "summary": "Unable to analyze this prescription. Please try again with a clearer image."
      }  