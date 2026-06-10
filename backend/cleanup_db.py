"""
cleanup_db.py - Remove test/junk documents from the vector store.
Only keeps the real uploaded research PDFs.
"""
import sys
sys.path.insert(0, '.')
from app.db.session import engine
from sqlalchemy import text

# Documents to remove (test artifacts from pytest + legacy rows)
TO_DELETE = [
    "legacy_document.pdf",  # auto-backfilled placeholder from migration
    "test_doc.txt",          # pytest upload test
    "test_readme.md",        # pytest upload test
    "test_upload.pdf",       # pytest upload test (copy of sample.pdf)
]

with engine.begin() as conn:
    for filename in TO_DELETE:
        count = conn.execute(
            text("SELECT COUNT(*) FROM documents WHERE filename = :f"),
            {"f": filename}
        ).scalar()

        if count > 0:
            conn.execute(
                text("DELETE FROM documents WHERE filename = :f"),
                {"f": filename}
            )
            print(f"  Deleted: {filename}  ({count} chunks removed)")
        else:
            print(f"  Not found (skipped): {filename}")

    # Show what's left
    remaining = conn.execute(text("""
        SELECT filename, file_type, COUNT(*) as chunks
        FROM documents
        GROUP BY filename, file_type
        ORDER BY filename
    """)).fetchall()

    print("\n=== Documents remaining in DB ===")
    for r in remaining:
        print(f"  [{r.file_type}] {r.filename}  ({r.chunks} chunks)")
