from app.rag.rag_service import RAGService


class RAGAgent:

    def __init__(self):
        self.rag = RAGService()

    def ask(self, question: str) -> dict:
        return self.rag.answer(question)
