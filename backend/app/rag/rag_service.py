"""
RAGService — retrieve relevant chunks and generate a grounded answer.

Handles both Q&A and summarization requests.
"""

from app.rag.retriever import Retriever
from app.services.llm_service import LLMService

# keywords that indicate the user wants a summary/overview (use more chunks)
SUMMARIZE_KEYWORDS = [
    "summarize", "summary", "overview", "brief", "outline",
    "main points", "key points", "what is this document",
    "what is the document about", "what does this document cover",
    "list all", "list the", "main sections", "sections in",
    "what are the topics", "give me an overview",
]


class RAGService:

    def __init__(self):
        self.retriever = Retriever()
        self.llm = LLMService()

    def answer(self, question: str) -> str:
        question_lower = question.lower()

        # use more chunks for summarization/overview requests
        is_summary = any(kw in question_lower for kw in SUMMARIZE_KEYWORDS)
        limit = 12 if is_summary else 5

        results = self.retriever.search(query=question, limit=limit)

        if not results:
            return (
                "No documents have been uploaded yet. "
                "Please upload a PDF, TXT, or DOCX file first using the Upload section."
            )

        # build context — label each chunk with its source
        context_parts = []
        seen_filenames = set()
        for i, row in enumerate(results, 1):
            fname = getattr(row, "filename", "document")
            seen_filenames.add(fname)
            context_parts.append(f"[Chunk {i} from '{fname}']:\n{row.content}")

        context = "\n\n---\n\n".join(context_parts)
        sources = ", ".join(seen_filenames)

        if is_summary:
            prompt = f"""You are an Enterprise AI assistant tasked with summarizing documents.

You have been given {len(results)} text chunks from the document(s): {sources}

Your task: {question}

Instructions:
- Use ALL the provided chunks to form a comprehensive response
- Organize your answer with clear sections or bullet points
- If listing sections, use the actual headings/topics you can identify in the content
- Be thorough but concise

Document Content:
{context}

Response:"""
        else:
            prompt = f"""You are an Enterprise AI assistant.

Use the provided document context to answer the question.
If the information is not clearly in the context, say what you DO know from the context
and note that the full answer may require reading more of the document.

Source document(s): {sources}

Context:
{context}

Question: {question}

Answer:"""

        return self.llm.generate(prompt)
