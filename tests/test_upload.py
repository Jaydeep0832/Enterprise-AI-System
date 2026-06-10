"""
test_upload.py — Tests for document upload and management API.

Tests:
  - Upload a PDF (using the sample.pdf in backend/)
  - Upload a TXT file
  - Upload unsupported type is rejected
  - GET /documents lists uploaded files
  - GET /documents/{id} retrieves a chunk
  - DELETE /documents/{filename} removes all chunks
"""

import io
import os

# Path to a real PDF for integration tests
SAMPLE_PDF = os.path.join(
    os.path.dirname(__file__), "..", "backend", "sample.pdf"
)


def test_upload_pdf_success(client):
    """Uploading a valid PDF should return success with chunk count."""
    if not os.path.exists(SAMPLE_PDF):
        import pytest
        pytest.skip("sample.pdf not found — skipping PDF upload test")

    with open(SAMPLE_PDF, "rb") as f:
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test_upload.pdf", f, "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"] == "test_upload.pdf"
    assert data["file_type"] == "pdf"
    assert data["chunks"] > 0
    assert data["size_bytes"] > 0


def test_upload_txt_success(client):
    """Uploading a TXT file should succeed."""
    content = b"This is a test document.\nIt has multiple lines.\nUsed for testing the upload pipeline."
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test_doc.txt", io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["file_type"] == "txt"
    assert data["chunks"] >= 1


def test_upload_md_success(client):
    """Uploading a Markdown file should succeed."""
    content = b"# Test Document\n\nThis is a markdown test file.\n\n## Section 2\n\nMore content here."
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test_readme.md", io.BytesIO(content), "text/markdown")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["file_type"] == "md"


def test_upload_unsupported_type_rejected(client):
    """Uploading an unsupported file type should return 400."""
    content = b"fake exe content"
    response = client.post(
        "/api/v1/upload",
        files={"file": ("virus.exe", io.BytesIO(content), "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]


def test_list_documents(client):
    """GET /documents should return a list of uploaded documents."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert isinstance(data["documents"], list)


def test_list_documents_has_metadata(client):
    """Each document entry should have filename, file_type, chunk_count, uploaded_at."""
    response = client.get("/api/v1/documents")
    data = response.json()

    if data["total"] > 0:
        doc = data["documents"][0]
        assert "filename" in doc
        assert "file_type" in doc
        assert "chunk_count" in doc
        assert "uploaded_at" in doc


def test_get_document_chunk_not_found(client):
    """GET /documents/99999999 should return 404."""
    response = client.get("/api/v1/documents/99999999")
    assert response.status_code == 404


def test_delete_nonexistent_document(client):
    """Deleting a filename that doesn't exist should return 404."""
    response = client.delete("/api/v1/documents/this_file_does_not_exist.pdf")
    assert response.status_code == 404


def test_upload_then_delete(client):
    """Upload a file, verify it appears in list, then delete it."""
    # upload
    content = b"This document will be deleted after test."
    response = client.post(
        "/api/v1/upload",
        files={"file": ("delete_me.txt", io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 200

    # verify it appears in list
    list_response = client.get("/api/v1/documents")
    filenames = [d["filename"] for d in list_response.json()["documents"]]
    assert "delete_me.txt" in filenames

    # delete it
    del_response = client.delete("/api/v1/documents/delete_me.txt")
    assert del_response.status_code == 200
    data = del_response.json()
    assert data["status"] == "deleted"
    assert data["filename"] == "delete_me.txt"
    assert data["chunks_deleted"] >= 1

    # verify it's gone
    list_response2 = client.get("/api/v1/documents")
    filenames2 = [d["filename"] for d in list_response2.json()["documents"]]
    assert "delete_me.txt" not in filenames2
