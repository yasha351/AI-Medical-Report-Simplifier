"""
test_ocr.py
------------
End-to-end manual test / demo script: OCR extraction + formatting.

Usage:
    python test_ocr.py <path_to_file>

If no path is provided, it defaults to the first file found in the
`sample_reports/` directory.

Pipeline:
    1. extract_text()  -> raw OCR text        (ocr_service.py)
    2. format_text()   -> formatted string     (formatter.py)
    3. Print the formatted output to the console.
    4. Save both outputs to disk:
        - output/raw_text.txt
        - output/formatted_output.txt
"""

import os
import sys

from formatter import format_text
from ocr_service import (
    OCRProcessingError,
    UnsupportedFileTypeError,
    extract_text,
)

# --------------------------------------------------------------------------
# Paths (relative to this file, so the script works regardless of the
# current working directory it's launched from).
# --------------------------------------------------------------------------
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_REPORTS_DIR = os.path.join(THIS_DIR, "sample_reports")
OUTPUT_DIR = os.path.join(THIS_DIR, "output")
RAW_TEXT_FILE = os.path.join(OUTPUT_DIR, "raw_text.txt")
FORMATTED_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "formatted_output.txt")


def _find_default_sample_file() -> str:
    """
    Locate the first supported file inside sample_reports/ to use as a
    default test input when no CLI argument is given.

    Returns:
        Path to a sample file.

    Raises:
        FileNotFoundError: If sample_reports/ is empty or missing.
    """
    supported_extensions = (".pdf", ".png", ".jpg", ".jpeg")

    if not os.path.isdir(SAMPLE_REPORTS_DIR):
        raise FileNotFoundError(
            f"Sample reports directory not found: {SAMPLE_REPORTS_DIR}"
        )

    for filename in sorted(os.listdir(SAMPLE_REPORTS_DIR)):
        if filename.lower().endswith(supported_extensions):
            return os.path.join(SAMPLE_REPORTS_DIR, filename)

    raise FileNotFoundError(
        f"No supported sample file (.pdf/.png/.jpg/.jpeg) found in "
        f"{SAMPLE_REPORTS_DIR}. Please add a sample file or pass a path "
        f"as a command line argument."
    )


def main() -> None:
    """Entry point: run OCR + formatting on a file and save both results."""

    # Step 1: Determine which file to run OCR on.
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        print(
            "No file path provided. Looking for a sample file in "
            f"'{SAMPLE_REPORTS_DIR}'..."
        )
        file_path = _find_default_sample_file()

    print(f"Running OCR on: {file_path}\n")

    # Step 2: Run OCR extraction.
    try:
        raw_text = extract_text(file_path)
    except FileNotFoundError as exc:
        print(f"[ERROR] File not found: {exc}")
        sys.exit(1)
    except UnsupportedFileTypeError as exc:
        print(f"[ERROR] Unsupported file type: {exc}")
        sys.exit(1)
    except OCRProcessingError as exc:
        print(f"[ERROR] OCR processing failed: {exc}")
        sys.exit(1)

    # Step 3: Format the extracted text.
    formatted_output = format_text(raw_text)

    # Step 4: Print the formatted output.
    print("----- FORMATTED OUTPUT -----")
    print(formatted_output if formatted_output else "(No content to display)")
    print("-----------------------------\n")

    # Step 5: Save both raw and formatted output to disk.
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(RAW_TEXT_FILE, "w", encoding="utf-8") as raw_file:
        raw_file.write(raw_text)

    with open(FORMATTED_OUTPUT_FILE, "w", encoding="utf-8") as formatted_file:
        formatted_file.write(formatted_output)

    print(f"Raw OCR text saved to:       {RAW_TEXT_FILE}")
    print(f"Formatted output saved to:   {FORMATTED_OUTPUT_FILE}")


if __name__ == "__main__":
    main()