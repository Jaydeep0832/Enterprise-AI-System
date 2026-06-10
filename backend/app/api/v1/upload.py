"""
Upload API — document upload with metadata + management endpoints.

Routes:
  POST   /upload                  — Upload a document (PDF, TXT, MD, DOCX)
  GET    /documents               — List all unique uploaded documents
  GET    /documents/{doc_id}      — Get a specific document chunk
  DELETE /documents/{filename}    — Delete all chunks for a document by filename
"""

import os

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import text

from app.db.session import SessionLocal, engine
from app.rag.document_ingestion import DocumentIngestion

router = APIRouter()

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "docx"}

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document and ingest it into the vector store."""
    ext = _get_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    content = await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    ingestion = DocumentIngestion()
    result = ingestion.ingest(file_path)

    return {
        "status": "success",
        "filename": result["filename"],
        "file_type": result["file_type"],
        "chunks": result["chunks"],
        "size_bytes": len(content),
    }


@router.get("/documents")
async def list_documents():
    """List all documents that have been uploaded (grouped by filename)."""
    sql = text("""
        SELECT
            filename,
            file_type,
            COUNT(*) AS chunk_count,
            MIN(uploaded_at) AS uploaded_at
        FROM documents
        GROUP BY filename, file_type
        ORDER BY uploaded_at DESC
    """)

    with engine.begin() as conn:
        rows = conn.execute(sql).fetchall()

    return {
        "documents": [
            {
                "filename": row.filename,
                "file_type": row.file_type,
                "chunk_count": row.chunk_count,
                "uploaded_at": str(row.uploaded_at),
            }
            for row in rows
        ],
        "total": len(rows),
    }


@router.get("/documents/{doc_id}")
async def get_document_chunk(doc_id: int):
    """Get a specific document chunk by its database ID."""
    sql = text("""
        SELECT id, filename, file_type, content, chunk_index, total_chunks, uploaded_at
        FROM documents
        WHERE id = :doc_id
    """)

    with engine.begin() as conn:
        row = conn.execute(sql, {"doc_id": doc_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Document chunk {doc_id} not found")

    return {
        "id": row.id,
        "filename": row.filename,
        "file_type": row.file_type,
        "content": row.content,
        "chunk_index": row.chunk_index,
        "total_chunks": row.total_chunks,
        "uploaded_at": str(row.uploaded_at),
    }


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete all chunks for a document by filename."""
    sql_count = text("SELECT COUNT(*) FROM documents WHERE filename = :filename")
    sql_delete = text("DELETE FROM documents WHERE filename = :filename")

    with engine.begin() as conn:
        count = conn.execute(sql_count, {"filename": filename}).scalar()
        if count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No document found with filename '{filename}'",
            )
        conn.execute(sql_delete, {"filename": filename})

    # also remove the file from disk if it exists
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    return {
        "status": "deleted",
        "filename": filename,
        "chunks_deleted": count,
    }
