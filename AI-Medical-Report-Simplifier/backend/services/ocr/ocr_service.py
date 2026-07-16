

import logging
import os
from typing import List

import fitz  # PyMuPDF - used to rasterize PDF pages into images
import numpy as np
from paddleocr import PaddleOCR

from preprocess import preprocess_image

# --------------------------------------------------------------------------
# Logging configuration
# --------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

# File extensions this service is able to process.
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS

# DPI used when rasterizing PDF pages to images. 300 DPI gives PaddleOCR
# enough resolution to read small print/table text reliably.
PDF_RENDER_DPI: int = 300


class UnsupportedFileTypeError(Exception):
    """Raised when a file with an unsupported extension is submitted."""


class OCRProcessingError(Exception):
    """Raised when OCR fails to process an image after preprocessing."""


# --------------------------------------------------------------------------
# PaddleOCR engine - initialized once (module-level singleton)
# --------------------------------------------------------------------------
# Initializing PaddleOCR loads detection + recognition models into memory.
# This is expensive, so we do it exactly once per process and reuse the
# same engine instance for every call to extract_text().
_ocr_engine: PaddleOCR = None


def _get_ocr_engine() -> PaddleOCR:
   
    global _ocr_engine
    if _ocr_engine is None:
        logger.info("Initializing PaddleOCR engine (first-time load)...")
        _ocr_engine = PaddleOCR(
            use_angle_cls=True,  # Detects and corrects rotated text lines.
            lang="en",           # Medical reports in this project are English.
            show_log=False,      # Keep PaddleOCR's internal logs quiet.
        )
        logger.info("PaddleOCR engine initialized successfully.")
    return _ocr_engine


# --------------------------------------------------------------------------
# File type helpers
# --------------------------------------------------------------------------

def _get_file_extension(file_path: str) -> str:
   
    _, ext = os.path.splitext(file_path)
    return ext.lower()


def is_pdf(file_path: str) -> bool:
    
    return _get_file_extension(file_path) in SUPPORTED_PDF_EXTENSIONS


def is_image(file_path: str) -> bool:
   
    return _get_file_extension(file_path) in SUPPORTED_IMAGE_EXTENSIONS


def validate_file(file_path: str) -> None:
    
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = _get_file_extension(file_path)
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext}'. "
            f"Supported types are: {sorted(SUPPORTED_EXTENSIONS)}"
        )


def convert_pdf_to_images(pdf_path: str) -> List[np.ndarray]:
   
    images: List[np.ndarray] = []

    try:
        pdf_document = fitz.open(pdf_path)
    except Exception as exc:
        raise OCRProcessingError(f"Failed to open PDF '{pdf_path}': {exc}") from exc

    try:
        # Zoom factor to achieve the desired render DPI.
        # PyMuPDF's default resolution is 72 DPI, so we scale accordingly.
        zoom = PDF_RENDER_DPI / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        for page_index in range(pdf_document.page_count):
            page = pdf_document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix)

            # Convert the PyMuPDF pixmap into a NumPy array.
            image_array = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
                pixmap.height, pixmap.width, pixmap.n
            )

            
            if pixmap.n == 1:
                image_bgr = cv2_gray_to_bgr(image_array)
            elif pixmap.n == 4:
                image_bgr = image_array[:, :, :3][:, :, ::-1]  # RGBA -> BGR
            else:
                image_bgr = image_array[:, :, ::-1]  # RGB -> BGR

            images.append(np.ascontiguousarray(image_bgr))
            logger.debug(
                "Rendered PDF page %d/%d as image with shape %s",
                page_index + 1,
                pdf_document.page_count,
                image_bgr.shape,
            )

    except Exception as exc:
        raise OCRProcessingError(
            f"Failed to render pages from PDF '{pdf_path}': {exc}"
        ) from exc
    finally:
        pdf_document.close()

    if not images:
        raise OCRProcessingError(f"PDF '{pdf_path}' contains no renderable pages.")

    return images


def cv2_gray_to_bgr(gray_array: np.ndarray) -> np.ndarray:
   
    if gray_array.ndim == 3 and gray_array.shape[2] == 1:
        gray_array = gray_array[:, :, 0]
    return np.stack([gray_array, gray_array, gray_array], axis=-1)


# --------------------------------------------------------------------------
# OCR execution
# --------------------------------------------------------------------------

def _run_ocr_on_image(image: np.ndarray) -> str:
   
    engine = _get_ocr_engine()

    try:
        # PaddleOCR expects a 3-channel image; convert single-channel
        # preprocessed images back to 3 channels for compatibility.
        if image.ndim == 2:
            ocr_input = cv2_gray_to_bgr(image)
        else:
            ocr_input = image

        result = engine.ocr(ocr_input, cls=True)
    except Exception as exc:
        raise OCRProcessingError(f"PaddleOCR failed to process image: {exc}") from exc

    lines: List[str] = []

    # PaddleOCR result structure: List[List[ [box, (text, confidence)] ]]
    # One outer list per image; we always pass a single image at a time.
    if result and result[0]:
        for detection in result[0]:
            if detection and len(detection) >= 2:
                text, _confidence = detection[1]
                if text and text.strip():
                    lines.append(text.strip())

    return "\n".join(lines)


# --------------------------------------------------------------------------
# Public interface
# --------------------------------------------------------------------------

def extract_text(file_path: str) -> str:
    
    logger.info("Starting OCR extraction for file: %s", file_path)

    # Step 1: Validate the incoming file.
    validate_file(file_path)

    # Step 2: Load page/image data depending on file type.
    if is_pdf(file_path):
        logger.info("Detected PDF file. Converting pages to images...")
        raw_images = convert_pdf_to_images(file_path)
    else:
        logger.info("Detected image file. Loading directly...")
        # Local import to avoid a circular/unused import at module load
        # time when only PDF functionality is exercised.
        from preprocess import load_image

        raw_images = [load_image(file_path)]

    logger.info("Loaded %d page(s)/image(s) for OCR.", len(raw_images))

    # Step 3: Preprocess each image and run OCR, collecting text per page.
    page_texts: List[str] = []
    for page_number, raw_image in enumerate(raw_images, start=1):
        logger.info("Processing page %d/%d...", page_number, len(raw_images))
        try:
            preprocessed = preprocess_image(raw_image)
            page_text = _run_ocr_on_image(preprocessed)
            page_texts.append(page_text)
        except OCRProcessingError:
            # Re-raise OCR errors as-is; they already carry useful context.
            raise
        except Exception as exc:
            raise OCRProcessingError(
                f"Unexpected error while processing page {page_number} "
                f"of '{file_path}': {exc}"
            ) from exc

    # Step 4: Combine all page texts into a single string.
    combined_text = "\n\n".join(text for text in page_texts if text)

    logger.info(
        "OCR extraction complete for '%s'. Extracted %d characters.",
        file_path,
        len(combined_text),
    )
    return combined_text
