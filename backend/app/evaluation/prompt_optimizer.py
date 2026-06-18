"""
prompt_optimizer.py — Feedback-driven prompt analysis and improvement.

Analyzes negative feedback patterns and generates prompt improvement suggestions
using LLM meta-analysis.
"""

import json
from typing import List, Dict

from app.services.llm_service import LLMService
from app.db.session import SessionLocal
from app.models.feedback import Feedback
from app.db.redis_client import redis_client
from app.memory.redis_memory import RedisMemory

llm = LLMService()


def analyze_negative_feedback(limit: int = 50) -> Dict:
    """
    Analyze recent negative feedback to identify common patterns.
    Returns categorized failure modes.
    """
    db = SessionLocal()
    try:
        negatives = (
            db.query(Feedback)
            .filter(Feedback.rating == -1)
            .order_by(Feedback.created_at.desc())
            .limit(limit)
            .all()
        )

        if not negatives:
            return {
                "total_negative": 0,
                "patterns": [],
                "message": "No negative feedback found.",
            }

        # Collect context: session messages that got negative feedback
        feedback_items = []
        for fb in negatives:
            # Try to get the actual conversation from Redis
            try:
                memory = RedisMemory(fb.session_id)
                history = memory.get_context()
                feedback_items.append({
                    "session_id": fb.session_id,
                    "message_index": fb.message_index,
                    "comment": fb.comment or "",
                    "context_preview": history[:500] if history else "",
                })
            except Exception:
                feedback_items.append({
                    "session_id": fb.session_id,
                    "message_index": fb.message_index,
                    "comment": fb.comment or "",
                    "context_preview": "",
                })

        # Use LLM to analyze patterns
        feedback_text = json.dumps(feedback_items[:20], indent=2)
        prompt = f"""Analyze these negative user feedback items from an AI assistant.
Identify common patterns, failure modes, and categories of bad responses.

Feedback items:
{feedback_text}

Return ONLY a JSON object:
{{
  "patterns": [
    {{
      "category": "category name",
      "description": "what went wrong",
      "frequency": "how common (high/medium/low)",
      "example_comment": "example user comment"
    }}
  ],
  "summary": "brief overall analysis"
}}"""

        try:
            response = llm.generate(prompt)
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                analysis = json.loads(match.group(0))
                analysis["total_negative"] = len(negatives)
                return analysis
        except Exception:
            pass

        return {
            "total_negative": len(negatives),
            "patterns": [],
            "summary": "Analysis failed — too few feedback items or LLM error.",
        }
    finally:
        db.close()


def generate_prompt_suggestions() -> Dict:
    """
    Generate LLM-powered prompt improvement suggestions based on negative feedback patterns.
    """
    analysis = analyze_negative_feedback()

    if not analysis.get("patterns"):
        return {
            "suggestions": [],
            "message": "Not enough negative feedback patterns to generate suggestions.",
        }

    patterns_text = json.dumps(analysis["patterns"], indent=2)
    prompt = f"""Based on these failure patterns from an Enterprise AI assistant, suggest specific prompt improvements.

The system uses different prompts for:
1. RAG (document Q&A) — stuffs retrieved chunks into a prompt
2. Research — synthesizes web search results
3. Tool Agent — decides which tool to call
4. Brainstorming — generates and critiques ideas
5. Router — classifies user intent

Failure patterns:
{patterns_text}

For each suggestion, specify which prompt to modify and the exact improvement.

Return ONLY a JSON object:
{{
  "suggestions": [
    {{
      "agent": "agent name (rag/research/tool/brainstorm/router)",
      "problem": "what the current prompt does wrong",
      "improvement": "specific prompt change to fix it",
      "priority": "high/medium/low"
    }}
  ]
}}"""

    try:
        response = llm.generate(prompt)
        import re
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass

    return {"suggestions": [], "message": "Failed to generate suggestions."}
