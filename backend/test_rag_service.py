from app.rag.rag_service import RAGService

rag = RAGService()

response = rag.answer(
    "What is MCP?"
)

print(response)
