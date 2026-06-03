from app.rag.retriever import Retriever
from app.services.llm_service import LLMService


class RAGService:

    def __init__(self):
        self.retriever = Retriever()
        self.llm = LLMService()

    def ask(self, question: str):

        docs = self.retriever.search(
            question,
            limit=3
        )

        context = "\n\n".join(
            doc[1]
            for doc in docs
        )

        prompt = f"""
        Answer the question using
        the provided context.

        Context:
        {context}

        Question:
        {question}
        """

        return self.llm.generate(
            prompt
        )
