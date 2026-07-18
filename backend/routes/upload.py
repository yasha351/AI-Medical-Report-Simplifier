# routes/upload.py
# ------------------------------------------------------------
# This file defines the /upload endpoint.
#
# Responsibilities:
#   - Create an APIRouter
#   - Receive the uploaded file from the HTTP request
#   - Delegate ALL processing to upload_controller.py
#   - Return whatever the controller returns
#
# NO validation, saving, or business logic belongs here.
# ------------------------------------------------------------

from fastapi import APIRouter, UploadFile, File
from controllers.upload_controller import handle_upload

# Create a router object.
# This acts like a "mini FastAPI app" that we plug into the main app
# via app.include_router() in app.py
router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint: POST /upload

    Accepts a single file from the client (form-data) and
    passes it to the upload controller for validation and saving.
    """
    # Delegate everything to the controller.
    # The route itself does NOT know how to validate or save files —
    # that separation is intentional (Single Responsibility Principle).
    result = await handle_upload(file)
    return result