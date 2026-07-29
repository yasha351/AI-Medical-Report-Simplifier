# app.py
# ------------------------------------------------------------
# This is the ENTRY POINT of the backend application.
# Its only job is to:
#   1. Create the FastAPI app instance
#   2. Register (include) routers from the routes/ folder
#   3. Provide a simple health-check root endpoint
#
# NO business logic should ever be written in this file.
# ------------------------------------------------------------

from fastapi import FastAPI
from routes.upload import router as upload_router

# Create the FastAPI application instance.
# This "app" object is what Uvicorn runs when we start the server.
app = FastAPI(
    title="AI Medical Report Simplifier",
    description="Backend API for Lab Reports, Prescriptions and Medical Images",
    version="1.0.0"
)

# Register the upload router.
# Everything defined inside routes/upload.py (e.g. POST /upload)
# now becomes part of this app.
app.include_router(upload_router)


# A simple root endpoint, useful to confirm the server is running.
@app.get("/")
def read_root():
    return {"message": "AI Medical Report Simplifier backend is running"}