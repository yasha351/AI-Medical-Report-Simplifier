import sys
import os

# parser.py, aliases.py, models.py, utils.py use plain imports like
# "from aliases import ..." -- these only work if the parser/ folder
# itself is on Python's import path. This line adds it.
PARSER_DIR = os.path.join(os.path.dirname(__file__), "..", "parser")
sys.path.insert(0, os.path.abspath(PARSER_DIR))

from parser import parse_lab_report
from services.llm.gemini_service import summarize_report

if __name__ == "__main__":
    sample_ocr_text = """
    Patient Name: John Doe
    Age: 45
    Gender: Male

    Hemoglobin      10.2 g/dL
    WBC             6200 /uL
    Platelets       250000 /uL
    Glucose         98 mg/dL
    """

    parsed_data = parse_lab_report(sample_ocr_text)
    print("Parsed data:", parsed_data)

    summary = summarize_report(parsed_data)
    print("\nLLM Summary:\n", summary)