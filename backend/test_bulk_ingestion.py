from app.rag.ingestion import IngestionService

service = IngestionService()

documents = [
    "Vector databases enable semantic search.",
    "Redis is an in-memory data store.",
    "PostgreSQL is a relational database.",
    "FastAPI is a Python web framework.",
    "RAG stands for Retrieval Augmented Generation.",
]

for doc in documents:
    result = service.ingest(doc)
    print(result)
