from app.rag.ingestion import IngestionService

service = IngestionService()

result = service.ingest(
    """
    Vector databases enable
    semantic search and RAG.
    """
)

print(result)
