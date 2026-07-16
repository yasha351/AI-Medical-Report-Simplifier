"""
preprocess.py
--------------
Image preprocessing utilities for the OCR module.

This module contains small, single-purpose functions that together form an
image preprocessing pipeline used before running PaddleOCR. Keeping each
step in its own function makes the pipeline easy to test, debug, and
reorder if needed.

All functions operate on / return NumPy arrays in OpenCV's BGR or
grayscale format (as documented per function).
"""

import logging
import os
from typing import Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Maximum dimension (width or height) allowed for an image before it is
# downscaled. This keeps OCR fast and memory-safe for very large scans.
MAX_DIMENSION: int = 2000

# Minimum dimension allowed before an image is upscaled. Very small images
# tend to produce poor OCR results, so we enlarge them a bit.
MIN_DIMENSION: int = 600


def load_image(image_path: str) -> np.ndarray:
    """
    Load an image from disk into a BGR NumPy array (OpenCV format).

    Args:
        image_path: Absolute or relative path to the image file.

    Returns:
        The loaded image as a NumPy array (BGR).

    Raises:
        FileNotFoundError: If the file does not exist on disk.
        ValueError: If OpenCV fails to decode the file as an image.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    image = cv2.imread(image_path, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError(
            f"Failed to read image (unsupported or corrupt file): {image_path}"
        )

    logger.debug("Loaded image '%s' with shape %s", image_path, image.shape)
    return image


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert a BGR image to single-channel grayscale.

    Args:
        image: Input image in BGR format.

    Returns:
        Grayscale image (single channel).
    """
    if image is None or image.size == 0:
        raise ValueError("Cannot convert an empty image to grayscale.")

    # If the image is already single-channel, return it unchanged.
    if len(image.shape) == 2:
        return image

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray


def denoise_image(gray_image: np.ndarray) -> np.ndarray:
    """
    Remove noise from a grayscale image using a fast Non-Local Means
    denoising filter. This helps eliminate scanner/camera speckle noise
    without destroying fine text edges.

    Args:
        gray_image: Single-channel grayscale image.

    Returns:
        Denoised grayscale image.
    """
    if gray_image is None or gray_image.size == 0:
        raise ValueError("Cannot denoise an empty image.")

    denoised = cv2.fastNlMeansDenoising(
        gray_image,
        h=10,            # Filter strength; higher removes more noise but
                         # may also remove fine text detail.
        templateWindowSize=7,
        searchWindowSize=21,
    )
    return denoised


def improve_contrast(gray_image: np.ndarray) -> np.ndarray:
    """
    Improve local contrast and binarize the image so text stands out
    clearly from the background. Uses CLAHE (Contrast Limited Adaptive
    Histogram Equalization) followed by adaptive thresholding, which
    performs well on medical reports with uneven lighting/scan quality.

    Args:
        gray_image: Single-channel grayscale image.

    Returns:
        A thresholded (binarized) image with improved contrast.
    """
    if gray_image is None or gray_image.size == 0:
        raise ValueError("Cannot improve contrast of an empty image.")

    # Step 1: Adaptive histogram equalization to boost local contrast.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(gray_image)

    # Step 2: Adaptive thresholding to binarize text against background.
    # Gaussian-weighted thresholding handles uneven lighting better than
    # a single global threshold.
    thresholded = cv2.adaptiveThreshold(
        contrast_enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )
    return thresholded


def resize_image(image: np.ndarray) -> np.ndarray:
    """
    Resize the image so its largest dimension does not exceed
    MAX_DIMENSION and its smallest dimension is not below MIN_DIMENSION.
    This keeps OCR both fast (on huge scans) and accurate (on tiny images).

    Args:
        image: Input image (grayscale or BGR).

    Returns:
        Resized image. If no resizing is required, the original image is
        returned unchanged.
    """
    if image is None or image.size == 0:
        raise ValueError("Cannot resize an empty image.")

    height, width = image.shape[:2]
    largest_dim = max(height, width)
    smallest_dim = min(height, width)

    scale: float = 1.0

    if largest_dim > MAX_DIMENSION:
        scale = MAX_DIMENSION / float(largest_dim)
    elif smallest_dim < MIN_DIMENSION:
        scale = MIN_DIMENSION / float(smallest_dim)

    if scale != 1.0:
        new_size: Tuple[int, int] = (
            max(1, int(width * scale)),
            max(1, int(height * scale)),
        )
        interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
        image = cv2.resize(image, new_size, interpolation=interpolation)
        logger.debug("Resized image to %s (scale=%.3f)", new_size, scale)

    return image


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Full preprocessing pipeline applied before OCR:
        1. Resize to a manageable resolution.
        2. Convert to grayscale.
        3. Denoise.
        4. Improve contrast / binarize.

    Args:
        image: Raw input image (BGR, as loaded from disk or rendered
            from a PDF page).

    Returns:
        A single-channel, denoised, contrast-enhanced image ready for
        PaddleOCR.
    """
    resized = resize_image(image)
    gray = convert_to_grayscale(resized)
    denoised = denoise_image(gray)
    final_image = improve_contrast(denoised)

    logger.debug("Preprocessing complete. Final image shape: %s", final_image.shape)
    return final_image