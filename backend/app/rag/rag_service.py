from app.rag.retriever import Retriever
from app.services.llm_service import LLMService


class RAGService:

    def __init__(self):
        self.retriever = Retriever()
        self.llm = LLMService()

    def answer(self, question: str) -> str:
        results = self.retriever.search(query=question, limit=5)

        context = "\n\n".join(row.content for row in results)

        prompt = f"""You are an Enterprise AI assistant.

Answer ONLY using the provided context.
If the answer cannot be found in the context, respond with:
"I could not find the answer in the uploaded documents."

Context:
{context}

Question:
{question}

Answer:"""

        return self.llm.generate(prompt)
