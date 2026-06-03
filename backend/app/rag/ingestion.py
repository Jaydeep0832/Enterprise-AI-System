from sqlalchemy import text

from app.db.session import engine
from app.rag.embedder import Embedder


class IngestionService:

    def __init__(self):
        self.embedder = Embedder()

    def ingest(self, content: str):

        embedding = self.embedder.embed(
            content
        )

        query = text("""
            INSERT INTO documents
            (content, embedding)
            VALUES
            (:content, :embedding)
        """)

        with engine.begin() as conn:

            conn.execute(
                query,
                {
                    "content": content,
                    "embedding": embedding
                }
            )

        return {
            "status": "stored",
            "dimensions": len(embedding)
        }
