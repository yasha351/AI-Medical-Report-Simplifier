# controllers/upload_controller.py
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException

from services.parser.lab_parser import parse_lab_report
from services.parser.prescription_parser_service import process_prescription

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 20 * 1024 * 1024
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"


async def handle_upload(file: UploadFile, upload_type: str = "lab"):
    # STEP 1: Validate file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return {"status": "error", "message": "Invalid file type"}

    # STEP 2: Validate file size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        return {"status": "error", "message": "File size exceeds 20 MB limit"}
    await file.seek(0)

    # STEP 3: Save file to disk
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination_path = UPLOAD_DIR / file.filename

    try:
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # STEP 4: Call the correct parser based on upload_type
    try:
        if upload_type == "prescription":
            structured_data = process_prescription(str(destination_path))
        else:
            structured_data = parse_lab_report(str(destination_path))
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Failed to process document: {exc}"
        }

    return {
        "status": "success",
        "filename": file.filename,
        "path": f"uploads/{file.filename}",
        "structured_data": structured_data,
        "message": "File processed successfully"
    }