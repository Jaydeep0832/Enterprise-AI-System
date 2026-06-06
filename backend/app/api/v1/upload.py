import os

from fastapi import APIRouter, File, UploadFile

from app.rag.document_ingestion import DocumentIngestion

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    ingestion = DocumentIngestion()
    chunks = ingestion.ingest_pdf(file_path)

    return {
        "filename": file.filename,
        "chunks": chunks,
        "status": "success",
    }
