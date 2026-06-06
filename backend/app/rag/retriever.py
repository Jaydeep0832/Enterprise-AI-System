from sqlalchemy import text

from app.db.session import engine
from app.rag.embedder import Embedder


class Retriever:

    def __init__(self):
        self.embedder = Embedder()

    def search(self, query: str, limit: int = 3):
        query_embedding = self.embedder.embed(query)

        sql = text("""
            SELECT id, content,
                   embedding <=> CAST(:embedding AS vector) AS distance
            FROM documents
            ORDER BY distance
            LIMIT :limit
        """)

        with engine.begin() as conn:
            result = conn.execute(sql, {
                "embedding": str(query_embedding),
                "limit": limit,
            })
            return result.fetchall()
