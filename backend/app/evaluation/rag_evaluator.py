"""
rag_evaluator.py — Automated RAG quality evaluation.

Implements five core metrics:
  1. Faithfulness  — Does the answer only use info from the context?
  2. Answer Relevancy — Is the answer relevant to the question?
  3. Context Precision — Are the retrieved chunks relevant?
  4. Context Recall — How much of the expected answer is covered?
  5. Hallucination Detection — Does the answer contain fabricated facts?

Uses LLM-as-judge for faithfulness, relevancy, and hallucination.
Uses embedding similarity for context precision.
"""

import json
from typing import Optional

from app.services.llm_service import LLMService
from app.rag.embedder import Embedder

llm = LLMService()
embedder = Embedder()


def _extract_score(response: str) -> float:
    """Extract a JSON score from an LLM response, with fallback."""
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(response[start:end])
            return min(1.0, max(0.0, float(result.get("score", 0.5))))
    except Exception:
        pass
    return 0.5


def evaluate_faithfulness(question: str, answer: str, context: str) -> float:
    """
    Score 0.0 to 1.0 — does the answer stay faithful to the provided context?
    Uses LLM-as-judge pattern.
    """
    prompt = f"""You are an expert evaluator. Score how faithful the answer is to the given context.

A faithful answer ONLY uses information present in the context. If the answer introduces facts not in the context, it is unfaithful.

Context:
{context[:3000]}

Question: {question}
Answer: {answer}

Respond with ONLY a JSON object: {{"score": 0.0 to 1.0, "reason": "brief explanation"}}"""

    try:
        response = llm.generate(prompt)
        return _extract_score(response)
    except Exception:
        return 0.5


def evaluate_relevancy(question: str, answer: str) -> float:
    """
    Score 0.0 to 1.0 — is the answer relevant to the question?
    """
    prompt = f"""You are an expert evaluator. Score how relevant the answer is to the question.

A relevant answer directly addresses what was asked. Off-topic or overly generic answers score low.

Question: {question}
Answer: {answer}

Respond with ONLY a JSON object: {{"score": 0.0 to 1.0, "reason": "brief explanation"}}"""

    try:
        response = llm.generate(prompt)
        return _extract_score(response)
    except Exception:
        return 0.5


def evaluate_context_precision(question: str, chunks: list[str]) -> float:
    """
    Score 0.0 to 1.0 — are the retrieved chunks relevant to the question?
    Uses embedding cosine similarity.
    """
    if not chunks:
        return 0.0

    try:
        import numpy as np
        query_emb = np.array(embedder.embed(question))
        scores = []
        for chunk in chunks[:5]:
            chunk_emb = np.array(embedder.embed(chunk))
            cos_sim = np.dot(query_emb, chunk_emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(chunk_emb) + 1e-8
            )
            scores.append(float(cos_sim))
        return round(sum(scores) / len(scores), 4)
    except Exception:
        return 0.5


def evaluate_context_recall(
    question: str, answer: str, expected_answer: str, context: str
) -> float:
    """
    Score 0.0 to 1.0 — how much of the expected answer can be attributed to the context?
    Higher score means the context contained the info needed for the expected answer.
    """
    if not expected_answer:
        return 0.5  # Can't evaluate without an expected answer

    prompt = f"""You are an expert evaluator. Score how much of the expected answer is supported by the given context.

For each claim in the expected answer, check if the context contains supporting evidence.
Score 1.0 if ALL claims are supported, 0.0 if NONE are supported.

Context:
{context[:3000]}

Expected Answer: {expected_answer}
Generated Answer: {answer}

Respond with ONLY a JSON object: {{"score": 0.0 to 1.0, "reason": "brief explanation"}}"""

    try:
        response = llm.generate(prompt)
        return _extract_score(response)
    except Exception:
        return 0.5


def evaluate_hallucination(question: str, answer: str, context: str) -> float:
    """
    Score 0.0 to 1.0 — how much of the answer is hallucinated (NOT in context)?
    0.0 = no hallucination (good), 1.0 = fully hallucinated (bad).
    We invert this so higher = better: 1.0 = no hallucination.
    """
    prompt = f"""You are an expert evaluator. Detect hallucination in the answer.

Compare the answer against the context. Identify any claims, facts, or details in the answer that are NOT present in the context.

Context:
{context[:3000]}

Question: {question}
Answer: {answer}

Score 0.0 if the answer is completely fabricated (all hallucinated).
Score 1.0 if every claim in the answer is supported by the context (no hallucination).

Respond with ONLY a JSON object: {{"score": 0.0 to 1.0, "reason": "brief explanation"}}"""

    try:
        response = llm.generate(prompt)
        return _extract_score(response)
    except Exception:
        return 0.5


def evaluate_rag_response(
    question: str,
    answer: str,
    context_chunks: list[str],
    expected_answer: str = "",
) -> dict:
    """
    Run all evaluation metrics on a single RAG response.
    Returns a dict with scores and an overall quality score.
    """
    context = "\n\n".join(context_chunks)

    faithfulness = evaluate_faithfulness(question, answer, context)
    relevancy = evaluate_relevancy(question, answer)
    precision = evaluate_context_precision(question, context_chunks)
    hallucination = evaluate_hallucination(question, answer, context)

    scores = {
        "faithfulness": round(faithfulness, 4),
        "answer_relevancy": round(relevancy, 4),
        "context_precision": round(precision, 4),
        "hallucination": round(hallucination, 4),
    }

    # Context recall only if expected answer is provided
    if expected_answer:
        recall = evaluate_context_recall(question, answer, expected_answer, context)
        scores["context_recall"] = round(recall, 4)
        overall = round(
            (faithfulness + relevancy + precision + hallucination + recall) / 5, 4
        )
    else:
        scores["context_recall"] = None
        overall = round(
            (faithfulness + relevancy + precision + hallucination) / 4, 4
        )

    scores["overall"] = overall
    return scores
