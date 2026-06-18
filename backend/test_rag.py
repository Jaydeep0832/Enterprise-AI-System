from app.rag.rag_service import RAGService

rag = RAGService()

response = rag.ask(
    "What enables semantic search?"
)

print(response)
