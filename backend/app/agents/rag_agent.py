from app.rag.rag_service import RAGService


class RAGAgent:

    def __init__(self):
        self.rag = RAGService()

    def ask(self, question: str) -> str:
        return self.rag.answer(question)
