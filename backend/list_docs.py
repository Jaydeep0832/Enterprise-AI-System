import sys
sys.path.insert(0, '.')
from app.db.session import engine
from sqlalchemy import text

# Show what's currently in the DB
with engine.begin() as conn:
    rows = conn.execute(text("""
        SELECT filename, file_type, COUNT(*) as chunks
        FROM documents
        GROUP BY filename, file_type
        ORDER BY filename
    """)).fetchall()
    print("=== Documents currently in DB ===")
    for r in rows:
        print(f"  [{r.file_type}] {r.filename}  ({r.chunks} chunks)")
