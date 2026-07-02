"""
Knowledge Graph API — build, query, and visualize the knowledge graph.

Routes:
  POST /kg/build          — Extract entities from all documents and build the graph
  GET  /kg/entities       — List/search entities
  GET  /kg/graph          — Full graph JSON for visualization
  POST /kg/query          — GraphRAG query (graph + vector combined)
  GET  /kg/stats          — Graph statistics
"""

from pydantic import BaseModel
from fastapi import APIRouter

from sqlalchemy import text
from app.db.session import engine
from app.knowledge_graph.entity_extractor import extract_entities_from_chunk
from app.knowledge_graph.graph_store import KnowledgeGraphStore
from app.knowledge_graph.graph_rag import GraphRAGService

router = APIRouter()


class KGQueryRequest(BaseModel):
    question: str


@router.post("/kg/build")
async def build_knowledge_graph():
    """
    Extract entities and relationships from all stored documents
    and build the knowledge graph.
    """
    # Fetch all document chunks
    sql = text("SELECT id, content, filename FROM documents ORDER BY id")
    with engine.begin() as conn:
        rows = conn.execute(sql).fetchall()

    if not rows:
        return {"error": "No documents found. Upload documents first."}

    kg = KnowledgeGraphStore()
    total_entities = 0
    total_relationships = 0
    processed_chunks = 0

    for row in rows:
        result = extract_entities_from_chunk(row.content, source_filename=row.filename)

        # Collect entities for batch insert
        entities_batch = []
        for entity in result.get("entities", []):
            entities_batch.append({
                "name": entity["name"],
                "entity_type": entity.get("type", "CONCEPT"),
                "description": entity.get("description", ""),
                "doc_source": entity.get("doc_source", row.filename),
            })
        
        # Collect relationships for batch insert
        relationships_batch = []
        for rel in result.get("relationships", []):
            relationships_batch.append({
                "source": rel["source"],
                "target": rel["target"],
                "relation": rel["relation"],
                "doc_source": rel.get("doc_source", row.filename),
            })

        # Batch insert — single transaction per chunk
        kg.add_entities_batch(entities_batch)
        kg.add_relationships_batch(relationships_batch)

        total_entities += len(entities_batch)
        total_relationships += len(relationships_batch)
        processed_chunks += 1

    return {
        "status": "complete",
        "chunks_processed": processed_chunks,
        "entities_extracted": total_entities,
        "relationships_extracted": total_relationships,
        "graph_stats": kg.get_stats(),
    }


@router.get("/kg/entities")
async def list_entities(search: str = ""):
    """List or search entities in the knowledge graph."""
    kg = KnowledgeGraphStore()
    if not kg._loaded:
        kg.load_from_db()

    if search:
        entities = kg.search_entities(search)
    else:
        entities = [
            {
                "name": name,
                "entity_type": data.get("entity_type", "unknown"),
                "description": data.get("description", ""),
            }
            for name, data in kg.graph.nodes(data=True)
        ]

    return {"entities": entities, "count": len(entities)}


@router.get("/kg/graph")
async def get_full_graph():
    """Return the full knowledge graph as JSON for frontend visualization."""
    kg = KnowledgeGraphStore()
    if not kg._loaded:
        kg.load_from_db()
    return kg.get_full_graph()


@router.post("/kg/query")
async def graph_rag_query(request: KGQueryRequest):
    """Run a GraphRAG query combining knowledge graph + vector retrieval."""
    kg = KnowledgeGraphStore()
    if not kg._loaded:
        kg.load_from_db()

    service = GraphRAGService()
    return service.query(request.question)


@router.get("/kg/stats")
async def graph_stats():
    """Get knowledge graph statistics."""
    kg = KnowledgeGraphStore()
    if not kg._loaded:
        kg.load_from_db()
    return kg.get_stats()
