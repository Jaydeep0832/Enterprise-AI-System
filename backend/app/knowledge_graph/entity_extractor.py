"""
entity_extractor.py — Extract entities and relationships from document chunks using LLM.

Processes document text and returns structured entity/relationship data
for building the knowledge graph.
"""

import json
import re
from typing import List, Dict

from app.services.llm_service import LLMService

llm = LLMService()


def extract_entities_from_chunk(chunk: str, source_filename: str = "unknown") -> Dict:
    """
    Use LLM to extract entities and relationships from a text chunk.
    Returns: {entities: [...], relationships: [...]}
    """
    prompt = f"""Extract all key entities and their relationships from the following text.

Return ONLY valid JSON in this exact format:
{{
  "entities": [
    {{"name": "Entity Name", "type": "PERSON|ORGANIZATION|TECHNOLOGY|CONCEPT|LOCATION|EVENT", "description": "brief description"}}
  ],
  "relationships": [
    {{"source": "Entity A", "target": "Entity B", "relation": "relation type (e.g., uses, part_of, created_by)"}}
  ]
}}

If no entities are found, return {{"entities": [], "relationships": []}}

Text:
{chunk[:2000]}"""

    try:
        response = llm.generate(prompt)
        # Extract JSON from response
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            # Add source to each entity and relationship
            for entity in data.get("entities", []):
                entity["doc_source"] = source_filename
            for rel in data.get("relationships", []):
                rel["doc_source"] = source_filename
            return data
    except Exception as e:
        print(f"[EntityExtractor] Warning: extraction failed: {e}")

    return {"entities": [], "relationships": []}


def extract_entities_from_question(question: str) -> List[str]:
    """
    Extract entity names from a user question for graph lookup.
    Uses a simpler prompt for speed.
    """
    prompt = f"""Extract the key entity names from this question. Return ONLY a JSON array of strings.
Example: ["Python", "machine learning", "Google"]

Question: {question}"""

    try:
        response = llm.generate(prompt)
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    return []
