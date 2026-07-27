import logging

from services.ocr.ocr_service import extract_text
from services.ocr.formatters.prescription_formatter import format_prescription
from services.parser.medicine_extractor import extract_medicines

logger = logging.getLogger(__name__)


def process_prescription(file_path: str) -> dict:
    """
    Runs the complete prescription pipeline.

    Image/PDF
        ↓
    OCR
        ↓
    Formatter
        ↓
    Medicine Extractor
        ↓
    JSON
    """

    try:
        # Step 1 - OCR
        raw_text = extract_text(file_path)

        if not raw_text or not raw_text.strip():
            logger.warning("OCR returned empty text.")
            return {"medicines": []}

        # Step 2 - Format OCR output
        formatted_table = format_prescription(raw_text)

        if formatted_table.startswith(
            "No medicine rows could be automatically detected."
        ):
            logger.warning("Formatter found no medicines.")
            return {"medicines": []}

        # Step 3 - Convert to JSON
        return extract_medicines(formatted_table)

    except Exception as e:
        logger.exception(e)
        return {"medicines": []}