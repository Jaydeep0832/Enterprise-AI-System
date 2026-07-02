"""
graph_store.py — Knowledge Graph storage using NetworkX + PostgreSQL.

NetworkX for in-memory graph operations (queries, pathfinding).
PostgreSQL for persistence (KGNode, KGEdge models).
"""

import networkx as nx
from typing import List, Dict, Optional

from app.db.session import SessionLocal
from app.models.knowledge_graph import KGNode, KGEdge


class KnowledgeGraphStore:
    """
    Singleton knowledge graph that combines NetworkX for
    fast in-memory queries with PostgreSQL for persistence.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.graph = nx.DiGraph()
            cls._instance._loaded = False
        return cls._instance

    def load_from_db(self):
        """Load the full graph from PostgreSQL into NetworkX."""
        db = SessionLocal()
        try:
            nodes = db.query(KGNode).all()
            edges = db.query(KGEdge).all()

            self.graph.clear()
            for node in nodes:
                self.graph.add_node(
                    node.name,
                    entity_type=node.entity_type,
                    description=node.description or "",
                    doc_source=node.doc_source or "",
                )
            for edge in edges:
                self.graph.add_edge(
                    edge.source_name,
                    edge.target_name,
                    relation=edge.relation,
                    doc_source=edge.doc_source or "",
                )
            self._loaded = True
        finally:
            db.close()

    # ── Single-item methods (kept for backward compatibility) ─────────────────

    def add_entity(self, name: str, entity_type: str, description: str = "", doc_source: str = ""):
        """Add an entity node to the graph and database."""
        # Add to NetworkX
        self.graph.add_node(
            name, entity_type=entity_type, description=description, doc_source=doc_source
        )

        # Persist to PostgreSQL (upsert logic)
        db = SessionLocal()
        try:
            existing = db.query(KGNode).filter(KGNode.name == name).first()
            if not existing:
                db.add(KGNode(
                    name=name, entity_type=entity_type,
                    description=description, doc_source=doc_source,
                ))
                db.commit()
        finally:
            db.close()

    def add_relationship(self, source: str, target: str, relation: str, doc_source: str = ""):
        """Add a relationship edge to the graph and database."""
        self.graph.add_edge(source, target, relation=relation, doc_source=doc_source)

        db = SessionLocal()
        try:
            existing = db.query(KGEdge).filter(
                KGEdge.source_name == source,
                KGEdge.target_name == target,
                KGEdge.relation == relation,
            ).first()
            if not existing:
                db.add(KGEdge(
                    source_name=source, target_name=target,
                    relation=relation, doc_source=doc_source,
                ))
                db.commit()
        finally:
            db.close()

    # ── Batch methods (single transaction per chunk) ─────────────────────────

    def add_entities_batch(self, entities: List[Dict]):
        """
        Add multiple entity nodes in a single database transaction.
        Each entity dict: {name, entity_type, description?, doc_source?}
        """
        if not entities:
            return

        # Add all to NetworkX first (fast, in-memory)
        for e in entities:
            self.graph.add_node(
                e["name"],
                entity_type=e.get("entity_type", "CONCEPT"),
                description=e.get("description", ""),
                doc_source=e.get("doc_source", ""),
            )

        # Batch persist to PostgreSQL — single transaction
        db = SessionLocal()
        try:
            # Fetch all existing names in one query
            names = [e["name"] for e in entities]
            existing = db.query(KGNode.name).filter(KGNode.name.in_(names)).all()
            existing_names = {row[0] for row in existing}

            # Insert only new entities
            new_entities = [
                KGNode(
                    name=e["name"],
                    entity_type=e.get("entity_type", "CONCEPT"),
                    description=e.get("description", ""),
                    doc_source=e.get("doc_source", ""),
                )
                for e in entities
                if e["name"] not in existing_names
            ]

            if new_entities:
                db.add_all(new_entities)
                db.commit()
        finally:
            db.close()

    def add_relationships_batch(self, relationships: List[Dict]):
        """
        Add multiple relationship edges in a single database transaction.
        Each relationship dict: {source, target, relation, doc_source?}
        """
        if not relationships:
            return

        # Add all to NetworkX first (fast, in-memory)
        for r in relationships:
            self.graph.add_edge(
                r["source"], r["target"],
                relation=r["relation"],
                doc_source=r.get("doc_source", ""),
            )

        # Batch persist to PostgreSQL — single transaction
        db = SessionLocal()
        try:
            # Build lookup keys for existing check
            new_edges = []
            for r in relationships:
                exists = db.query(KGEdge.id).filter(
                    KGEdge.source_name == r["source"],
                    KGEdge.target_name == r["target"],
                    KGEdge.relation == r["relation"],
                ).first()
                if not exists:
                    new_edges.append(KGEdge(
                        source_name=r["source"],
                        target_name=r["target"],
                        relation=r["relation"],
                        doc_source=r.get("doc_source", ""),
                    ))

            if new_edges:
                db.add_all(new_edges)
                db.commit()
        finally:
            db.close()

    # ── Query methods ────────────────────────────────────────────────────────

    def query_neighbors(self, entity_name: str, depth: int = 1) -> Dict:
        """Get all entities connected to the given entity within N hops."""
        if entity_name not in self.graph:
            return {"entity": entity_name, "neighbors": [], "edges": []}

        # Get subgraph within depth
        neighbors = set()
        edges = []
        visited = {entity_name}
        frontier = {entity_name}

        for _ in range(depth):
            next_frontier = set()
            for node in frontier:
                for successor in self.graph.successors(node):
                    if successor not in visited:
                        next_frontier.add(successor)
                        visited.add(successor)
                    edge_data = self.graph.get_edge_data(node, successor)
                    edges.append({
                        "source": node, "target": successor,
                        "relation": edge_data.get("relation", "related_to"),
                    })
                for predecessor in self.graph.predecessors(node):
                    if predecessor not in visited:
                        next_frontier.add(predecessor)
                        visited.add(predecessor)
                    edge_data = self.graph.get_edge_data(predecessor, node)
                    edges.append({
                        "source": predecessor, "target": node,
                        "relation": edge_data.get("relation", "related_to"),
                    })
            neighbors.update(next_frontier)
            frontier = next_frontier

        neighbor_data = []
        for n in neighbors:
            node_data = self.graph.nodes.get(n, {})
            neighbor_data.append({
                "name": n,
                "entity_type": node_data.get("entity_type", "unknown"),
                "description": node_data.get("description", ""),
            })

        return {"entity": entity_name, "neighbors": neighbor_data, "edges": edges}

    def search_entities(self, query: str) -> List[Dict]:
        """Find entities matching a text query (case-insensitive substring)."""
        query_lower = query.lower()
        results = []
        for name, data in self.graph.nodes(data=True):
            if query_lower in name.lower() or query_lower in data.get("description", "").lower():
                results.append({
                    "name": name,
                    "entity_type": data.get("entity_type", "unknown"),
                    "description": data.get("description", ""),
                    "doc_source": data.get("doc_source", ""),
                })
        return results

    def get_full_graph(self) -> Dict:
        """Return the entire graph as JSON for frontend visualization."""
        nodes = []
        for name, data in self.graph.nodes(data=True):
            nodes.append({
                "id": name,
                "name": name,
                "type": data.get("entity_type", "unknown"),
                "description": data.get("description", ""),
                "doc_source": data.get("doc_source", ""),
            })

        edges = []
        for src, tgt, data in self.graph.edges(data=True):
            edges.append({
                "source": src,
                "target": tgt,
                "relation": data.get("relation", "related_to"),
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def get_stats(self) -> Dict:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "loaded": self._loaded,
        }
