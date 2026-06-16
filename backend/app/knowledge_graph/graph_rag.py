"""
graph_rag.py — Graph-augmented Retrieval (GraphRAG).

Combines knowledge graph context with vector search for richer,
more structured answers to complex queries.
"""

from app.knowledge_graph.entity_extractor import extract_entities_from_question
from app.knowledge_graph.graph_store import KnowledgeGraphStore
from app.rag.retriever import Retriever
from app.services.llm_service import LLMService


class GraphRAGService:
    """
    GraphRAG pipeline:
      1. Extract entities from the user's question
      2. Query the knowledge graph for related context
      3. Combine graph context with vector retrieval
      4. Generate answer using enriched context
    """

    def __init__(self):
        self.kg = KnowledgeGraphStore()
        self.retriever = Retriever()
        self.llm = LLMService()

    def query(self, question: str) -> dict:
        """Run a GraphRAG query — graph context + vector search combined."""

        # Step 1: Extract entities from the question
        entities = extract_entities_from_question(question)

        # Step 2: Get graph context for each entity
        graph_context_parts = []
        graph_entities = []
        for entity in entities[:5]:  # Limit to 5 entities
            result = self.kg.query_neighbors(entity, depth=1)
            if result["neighbors"]:
                graph_entities.append(entity)
                for neighbor in result["neighbors"]:
                    graph_context_parts.append(
                        f"- {entity} → {neighbor['name']} ({neighbor['entity_type']}): {neighbor['description']}"
                    )
                for edge in result["edges"]:
                    graph_context_parts.append(
                        f"  Relationship: {edge['source']} --[{edge['relation']}]--> {edge['target']}"
                    )

        graph_context = "\n".join(graph_context_parts) if graph_context_parts else "No graph context available."

        # Step 3: Vector retrieval (standard RAG)
        vector_results = self.retriever.search(query=question, limit=5)
        vector_context = "\n\n".join([
            f"[Document: {getattr(r, 'filename', 'unknown')}]\n{r.content}"
            for r in vector_results
        ]) if vector_results else "No document context available."

        # Step 4: Generate answer with combined context
        prompt = f"""You are an Enterprise AI assistant with access to both a Knowledge Graph and Document Store.

Knowledge Graph Context (entities and relationships):
{graph_context}

Document Context (retrieved chunks):
{vector_context}

Question: {question}

Instructions:
- Use BOTH the knowledge graph relationships AND document context to answer
- If the graph shows entity relationships, mention how entities are connected
- Cite document sources when using document context
- Be comprehensive but concise

Answer:"""

        answer = self.llm.generate(prompt)

        sources = []
        if vector_results:
            for r in vector_results:
                sources.append({
                    "filename": getattr(r, "filename", "unknown"),
                    "chunk_index": getattr(r, "chunk_index", 0),
                    "content": r.content[:200],
                })

        return {
            "answer": answer,
            "sources": sources,
            "graph_entities": graph_entities,
            "graph_context": graph_context_parts,
        }
