from sqlalchemy import text

from app.db.session import engine
from app.rag.embedder import Embedder


class Retriever:

    def __init__(self):
        self.embedder = Embedder()

    def search(self, query: str, limit: int = 3):
        query_embedding = self.embedder.embed(query)

        sql = text("""
            WITH semantic_search AS (
                SELECT id, content, filename, chunk_index, embedding <=> CAST(:embedding AS vector) AS distance,
                       RANK() OVER (ORDER BY embedding <=> CAST(:embedding AS vector)) AS rank
                FROM documents
                ORDER BY distance
                LIMIT :limit
            ),
            keyword_search AS (
                SELECT id, content, filename, chunk_index, ts_rank(search_vector, websearch_to_tsquery('english', :query)) AS rank_score,
                       RANK() OVER (ORDER BY ts_rank(search_vector, websearch_to_tsquery('english', :query)) DESC) AS rank
                FROM documents
                WHERE search_vector @@ websearch_to_tsquery('english', :query)
                ORDER BY rank_score DESC
                LIMIT :limit
            )
            SELECT
                COALESCE(s.id, k.id) AS id,
                COALESCE(s.content, k.content) AS content,
                COALESCE(s.filename, k.filename) AS filename,
                COALESCE(s.chunk_index, k.chunk_index) AS chunk_index,
                COALESCE(1.0 / (60 + s.rank), 0.0) + COALESCE(1.0 / (60 + k.rank), 0.0) AS rrf_score
            FROM semantic_search s
            FULL OUTER JOIN keyword_search k ON s.id = k.id
            ORDER BY rrf_score DESC
            LIMIT :limit
        """)

        with engine.begin() as conn:
            result = conn.execute(sql, {
                "query": query,
                "embedding": str(query_embedding),
                "limit": limit,
            })
            return result.fetchall()
