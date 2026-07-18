# controllers/upload_controller.py
# ------------------------------------------------------------
# This file contains ALL business logic for handling file uploads.
#
# Responsibilities:
#   - Validate file extension (whitelist)
#   - Validate file size (max 20 MB)
#   - Create the uploads/ folder if missing
#   - Save the file to disk
#   - Return a JSON response (success or error)
#
# routes/upload.py calls this file. It does NOT know how this works.
# ------------------------------------------------------------

import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException

# ------------------------------------------------------------
# Configuration constants
# ------------------------------------------------------------

# Only these file extensions are allowed to be uploaded.
# Anything else (.exe, .zip, .rar, .txt, etc.) will be rejected.
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

# Maximum allowed file size: 20 MB, converted to bytes.
MAX_FILE_SIZE = 20 * 1024 * 1024

# The folder where all uploaded files will be stored.
# Path(__file__).resolve() gives the absolute path of THIS file.
# .parent takes us out of controllers/ into the backend/ root.
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"


async def handle_upload(file: UploadFile):
    """
    Validates and saves an uploaded file.

    Steps:
        1. Check the file extension is allowed
        2. Check the file size does not exceed the limit
        3. Ensure the uploads/ folder exists
        4. Save the file to disk
        5. Return a JSON-friendly dictionary response
    """

    # STEP 1: Validate file extension
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        return {
            "status": "error",
            "message": "Invalid file type"
        }

    # STEP 2: Validate file size
    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size > MAX_FILE_SIZE:
        return {
            "status": "error",
            "message": "File size exceeds 20 MB limit"
        }

    # Reset the file pointer back to the beginning.
    # We already consumed the stream above with file.read(),
    # so without this, saving the file would write an empty file.
    await file.seek(0)

    # STEP 3: Ensure uploads/ folder exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # STEP 4: Save the file to disk
    destination_path = UPLOAD_DIR / file.filename

    try:
        with open(destination_path, "wb") as buffer:
            # shutil.copyfileobj streams the file in chunks
            # instead of loading it all into memory at once.
            shutil.copyfileobj(file.file, buffer)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to save uploaded file"
        )

    # STEP 5: Return success response
    return {
        "status": "success",
        "filename": file.filename,
        "path": f"uploads/{file.filename}",
        "message": "File uploaded successfully"
    }