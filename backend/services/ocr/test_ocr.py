"""
test_ocr.py
------------
Simple manual test / demo script for the OCR service.

Usage:
    python test_ocr.py <path_to_file>

If no path is provided, it defaults to the first file found in the
`sample_reports/` directory.

What it does:
    1. Calls extract_text() from ocr_service.py.
    2. Prints the extracted text to the console.
    3. Saves the extracted text into output/report.txt.
"""

import os
import sys

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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "report.txt")


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
    """Entry point: run OCR on a file and save the result."""

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
        extracted_text = extract_text(file_path)
    except FileNotFoundError as exc:
        print(f"[ERROR] File not found: {exc}")
        sys.exit(1)
    except UnsupportedFileTypeError as exc:
        print(f"[ERROR] Unsupported file type: {exc}")
        sys.exit(1)
    except OCRProcessingError as exc:
        print(f"[ERROR] OCR processing failed: {exc}")
        sys.exit(1)

    # Step 3: Print the extracted text.
    print("----- EXTRACTED TEXT -----")
    print(extracted_text if extracted_text else "(No text detected)")
    print("---------------------------\n")

    # Step 4: Save the extracted text to output/report.txt.
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as output_file:
        output_file.write(extracted_text)

    print(f"Extracted text saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()