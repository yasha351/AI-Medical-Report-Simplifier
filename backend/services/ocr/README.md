# OCR Module — AI-Powered Medical Report Simplifier

This module is the **OCR (Optical Character Recognition) service** for the
AI-Powered Medical Report Simplifier project. It is owned by **Person 1**
of the team and is responsible **only** for converting an uploaded medical
document (Lab Report or Prescription, as PDF/PNG/JPG/JPEG) into raw text.

> This module does **not** parse text into structured JSON, call any LLM,
> talk to a database, or handle authentication. Those responsibilities
> belong to other modules built by the rest of the team.

## Public Interface

```python
from ocr_service import extract_text

text: str = extract_text("path/to/report.pdf")
```

`extract_text(file_path: str) -> str` is the **only** function the
integration team needs to call. It returns a single string containing all
text detected in the document.

---

## 1. Folder Structure

```
backend/
└── services/
    └── ocr/
        ├── ocr_service.py     # Main OCR logic + extract_text() entry point
        ├── preprocess.py      # Image preprocessing pipeline
        ├── test_ocr.py        # Manual test/demo script
        ├── requirements.txt   # Python dependencies
        ├── README.md          # This file
        ├── sample_reports/    # Put sample PDFs/images here for testing
        └── output/            # Extracted text is saved here (report.txt)
```

---

## 2. Prerequisites

- Python **3.9 – 3.11** recommended (PaddleOCR/PaddlePaddle compatibility).
- pip (latest version recommended).
- No external system binaries are required — PDF rendering uses **PyMuPDF**,
  which ships its own PDF engine (no Poppler installation needed).

---

## 3. Installation

### Step 1: Navigate to the OCR module folder

```bash
cd backend/services/ocr
```

### Step 2: Create a virtual environment

**On macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

You should see `(venv)` appear at the start of your terminal prompt once
activated.

### Step 3: Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note:** `paddlepaddle` and `paddleocr` are large packages and the
> first install may take several minutes. The very first time
> `extract_text()` runs, PaddleOCR will also download its detection and
> recognition model weights (a few hundred MB) — this requires an internet
> connection the first time only; models are cached locally afterward.

---

## 4. Running the Project

### Add a sample file

Place a sample lab report or prescription (PDF, PNG, JPG, or JPEG) inside
the `sample_reports/` folder, for example:

```
sample_reports/blood_report.pdf
```

### Run the test script

```bash
python test_ocr.py sample_reports/blood_report.pdf
```

If you don't pass a path, the script automatically picks the first
supported file it finds in `sample_reports/`:

```bash
python test_ocr.py
```

### Using it as a module in your own code

```python
from ocr_service import extract_text

text = extract_text("sample_reports/blood_report.pdf")
print(text)
```

---

## 5. Testing

`test_ocr.py` is the provided manual test script. Running it will:

1. Call `extract_text()` on the given file.
2. Print the extracted text to the console.
3. Save the extracted text to `output/report.txt`.

```bash
python test_ocr.py sample_reports/blood_report.pdf
```

Expected console output pattern:

```
Running OCR on: sample_reports/blood_report.pdf

----- EXTRACTED TEXT -----
Hemoglobin : 10.5
WBC : 6200
Platelets : 250000
---------------------------

Extracted text saved to: .../output/report.txt
```

---

## 6. Expected Output

Given an input file such as `blood_report.pdf`, `extract_text()` returns a
**single string** with one detected line of text per line, for example:

**Input:** `blood_report.pdf`

**Output (`output/report.txt`):**
```
Hemoglobin : 10.5
WBC : 6200
Platelets : 250000
```

If the input is a multi-page PDF, each page's text is separated by a blank
line within the same returned string.

---

## 7. Module Overview

### `preprocess.py`
Contains the image preprocessing pipeline used before OCR:
- `load_image()` — loads an image file into memory.
- `convert_to_grayscale()` — converts BGR images to grayscale.
- `denoise_image()` — removes scan/camera noise.
- `improve_contrast()` — enhances contrast and binarizes text.
- `resize_image()` — resizes images to an OCR-friendly resolution.
- `preprocess_image()` — runs the full pipeline in order.

### `ocr_service.py`
Contains the main OCR service:
- `extract_text(file_path)` — **public interface**; validates the file,
  handles PDF vs. image input, preprocesses each page, runs PaddleOCR, and
  returns all extracted text as a single combined string.
- `is_pdf()` / `is_image()` — file type detection helpers.
- `convert_pdf_to_images()` — rasterizes PDF pages into images using
  PyMuPDF.
- Custom exceptions: `UnsupportedFileTypeError`, `OCRProcessingError`.

### `test_ocr.py`
Command-line script for manually testing the service end-to-end.

---

## 8. Error Handling

`extract_text()` raises clear, specific exceptions so calling code
(FastAPI routes, other modules) can handle failures gracefully:

| Exception                     | Raised When                                      |
|--------------------------------|---------------------------------------------------|
| `FileNotFoundError`            | The given file path does not exist.               |
| `UnsupportedFileTypeError`     | The file extension isn't PDF/PNG/JPG/JPEG.         |
| `OCRProcessingError`           | PDF rendering or PaddleOCR processing fails.       |

---

## 9. Notes for the Integration Team

- Import only what you need: `from ocr_service import extract_text`.
- The function is synchronous (blocking). If calling it from an async
  FastAPI route, run it in a thread pool executor (e.g.
  `await run_in_threadpool(extract_text, file_path)`) to avoid blocking
  the event loop, since OCR is CPU-bound.
- The PaddleOCR engine is initialized **once** per process (lazy
  singleton) to avoid reloading models on every call.
- Output is **plain text only** — no JSON structuring is performed here;
  that is the parser module's responsibility.