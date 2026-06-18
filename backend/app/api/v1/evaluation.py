"""
Evaluation API — trigger and view RAG evaluation results.

Routes:
  POST /eval/dataset           — Add a question to the evaluation dataset
  GET  /eval/dataset           — List all evaluation dataset items
  PUT  /eval/dataset/{index}   — Update an evaluation item
  DELETE /eval/dataset/{index} — Remove an evaluation item
  POST /eval/dataset/import    — Bulk import evaluation items from JSON
  GET  /eval/dataset/export    — Export evaluation dataset as JSON
  POST /eval/run               — Run evaluation on stored dataset
  GET  /eval/results           — Get latest evaluation results
  GET  /eval/history           — List past evaluation runs
  GET  /eval/trends            — Show metric trends over time
  GET  /eval/alerts            — Get active quality alerts
"""

import json
from typing import Optional, List
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException

from app.db.redis_client import redis_client
from app.db.session import SessionLocal
from app.rag.rag_service import RAGService
from app.evaluation.rag_evaluator import evaluate_rag_response
from app.models.evaluation import EvalRun, EvalResult

router = APIRouter()

EVAL_DATASET_KEY = "eval:dataset"
EVAL_RESULTS_KEY = "eval:results"


# ── Dataset Management ───────────────────────────────────────────────────────


class EvalDatasetItem(BaseModel):
    question: str
    expected_answer: str = ""


class EvalDatasetImport(BaseModel):
    items: List[EvalDatasetItem]


@router.post("/eval/dataset")
async def add_eval_item(item: EvalDatasetItem):
    """Add a question to the evaluation dataset."""
    redis_client.rpush(EVAL_DATASET_KEY, json.dumps(item.model_dump()))
    return {"status": "added", "question": item.question}


@router.get("/eval/dataset")
async def get_eval_dataset():
    """List all evaluation dataset items."""
    items = redis_client.lrange(EVAL_DATASET_KEY, 0, -1)
    return {"dataset": [json.loads(i) for i in items], "count": len(items)}


@router.put("/eval/dataset/{index}")
async def update_eval_item(index: int, item: EvalDatasetItem):
    """Update an existing evaluation item by index."""
    total = redis_client.llen(EVAL_DATASET_KEY)
    if index < 0 or index >= total:
        raise HTTPException(status_code=404, detail=f"Index {index} out of range (0-{total-1})")
    redis_client.lset(EVAL_DATASET_KEY, index, json.dumps(item.model_dump()))
    return {"status": "updated", "index": index}


@router.delete("/eval/dataset/{index}")
async def delete_eval_item(index: int):
    """Remove an evaluation item by index (uses tombstone + cleanup pattern)."""
    total = redis_client.llen(EVAL_DATASET_KEY)
    if index < 0 or index >= total:
        raise HTTPException(status_code=404, detail=f"Index {index} out of range (0-{total-1})")

    tombstone = "__DELETED__"
    redis_client.lset(EVAL_DATASET_KEY, index, tombstone)
    redis_client.lrem(EVAL_DATASET_KEY, 1, tombstone)
    return {"status": "deleted", "index": index}


@router.post("/eval/dataset/import")
async def import_eval_dataset(data: EvalDatasetImport):
    """Bulk import evaluation items from a JSON array."""
    for item in data.items:
        redis_client.rpush(EVAL_DATASET_KEY, json.dumps(item.model_dump()))
    return {"status": "imported", "count": len(data.items)}


@router.get("/eval/dataset/export")
async def export_eval_dataset():
    """Export the full evaluation dataset as JSON."""
    items = redis_client.lrange(EVAL_DATASET_KEY, 0, -1)
    return {"items": [json.loads(i) for i in items]}


# ── Evaluation Execution ─────────────────────────────────────────────────────


@router.post("/eval/run")
async def run_evaluation():
    """
    Run RAG evaluation on all dataset questions.
    Each question is sent through the RAG pipeline and evaluated.
    Results are persisted to PostgreSQL.
    """
    items = redis_client.lrange(EVAL_DATASET_KEY, 0, -1)
    if not items:
        return {"error": "No evaluation dataset items. Add questions first via POST /eval/dataset."}

    rag = RAGService()
    results = []

    for raw in items:
        item = json.loads(raw)
        question = item["question"]
        expected_answer = item.get("expected_answer", "")

        # Run RAG pipeline
        rag_result = rag.answer(question)
        answer = rag_result["answer"]
        sources = rag_result.get("sources", [])
        chunks = [s.get("content", "") for s in sources if isinstance(s, dict)]

        # Evaluate
        scores = evaluate_rag_response(
            question, answer, chunks, expected_answer=expected_answer
        )
        scores["question"] = question
        scores["answer_preview"] = answer[:200]
        scores["num_sources"] = len(sources)
        results.append(scores)

    # Calculate averages
    avg = {
        "faithfulness": round(sum(r["faithfulness"] for r in results) / len(results), 4),
        "answer_relevancy": round(sum(r["answer_relevancy"] for r in results) / len(results), 4),
        "context_precision": round(sum(r["context_precision"] for r in results) / len(results), 4),
        "hallucination": round(sum(r["hallucination"] for r in results) / len(results), 4),
        "overall": round(sum(r["overall"] for r in results) / len(results), 4),
    }

    # Context recall average (only for items that have it)
    recall_values = [r["context_recall"] for r in results if r.get("context_recall") is not None]
    if recall_values:
        avg["context_recall"] = round(sum(recall_values) / len(recall_values), 4)

    output = {"averages": avg, "details": results, "count": len(results)}

    # Store in Redis (latest)
    redis_client.set(EVAL_RESULTS_KEY, json.dumps(output))

    # Persist to PostgreSQL
    db = SessionLocal()
    try:
        run = EvalRun(
            dataset_size=len(results),
            avg_faithfulness=avg["faithfulness"],
            avg_relevancy=avg["answer_relevancy"],
            avg_precision=avg["context_precision"],
            avg_overall=avg["overall"],
            status="completed",
        )
        db.add(run)
        db.flush()  # Get the run.id

        for r in results:
            db.add(EvalResult(
                eval_run_id=run.id,
                question=r["question"],
                answer_preview=r.get("answer_preview", ""),
                faithfulness=r["faithfulness"],
                answer_relevancy=r["answer_relevancy"],
                context_precision=r["context_precision"],
                hallucination=r.get("hallucination", 0),
                context_recall=r.get("context_recall"),
                overall=r["overall"],
                num_sources=r.get("num_sources", 0),
            ))
        db.commit()
        output["run_id"] = run.id
    except Exception as e:
        db.rollback()
        output["persistence_warning"] = f"Results computed but failed to persist: {e}"
    finally:
        db.close()

    return output


@router.get("/eval/results")
async def get_eval_results():
    """Get the latest evaluation results."""
    raw = redis_client.get(EVAL_RESULTS_KEY)
    if not raw:
        return {"message": "No evaluation results yet. Run POST /eval/run first."}
    return json.loads(raw)


# ── History & Trends ──────────────────────────────────────────────────────────


@router.get("/eval/history")
async def get_eval_history(limit: int = 20):
    """List past evaluation runs with average scores."""
    db = SessionLocal()
    try:
        runs = db.query(EvalRun).order_by(EvalRun.created_at.desc()).limit(limit).all()
        return {
            "runs": [
                {
                    "id": r.id,
                    "dataset_size": r.dataset_size,
                    "avg_faithfulness": r.avg_faithfulness,
                    "avg_relevancy": r.avg_relevancy,
                    "avg_precision": r.avg_precision,
                    "avg_overall": r.avg_overall,
                    "status": r.status,
                    "created_at": str(r.created_at),
                }
                for r in runs
            ],
            "count": len(runs),
        }
    finally:
        db.close()


@router.get("/eval/trends")
async def get_eval_trends():
    """Show metric trends over time from evaluation history."""
    db = SessionLocal()
    try:
        runs = db.query(EvalRun).order_by(EvalRun.created_at.asc()).limit(50).all()
        if not runs:
            return {"message": "No evaluation history. Run POST /eval/run at least twice to see trends."}

        return {
            "labels": [str(r.created_at.date()) for r in runs],
            "faithfulness": [r.avg_faithfulness for r in runs],
            "relevancy": [r.avg_relevancy for r in runs],
            "precision": [r.avg_precision for r in runs],
            "overall": [r.avg_overall for r in runs],
        }
    finally:
        db.close()


# ── Quality Alerts ────────────────────────────────────────────────────────────


@router.get("/eval/alerts")
async def get_quality_alerts():
    """
    Compare the two most recent evaluation runs.
    Flag regressions when any metric drops by >10%.
    """
    db = SessionLocal()
    try:
        runs = db.query(EvalRun).order_by(EvalRun.created_at.desc()).limit(2).all()
        if len(runs) < 2:
            return {"alerts": [], "message": "Need at least 2 evaluation runs to detect regressions."}

        current, previous = runs[0], runs[1]
        alerts = []

        metrics = [
            ("faithfulness", current.avg_faithfulness, previous.avg_faithfulness),
            ("relevancy", current.avg_relevancy, previous.avg_relevancy),
            ("precision", current.avg_precision, previous.avg_precision),
            ("overall", current.avg_overall, previous.avg_overall),
        ]

        for name, curr_val, prev_val in metrics:
            if prev_val > 0:
                change_pct = ((curr_val - prev_val) / prev_val) * 100
                if change_pct < -10:
                    alerts.append({
                        "metric": name,
                        "severity": "critical" if change_pct < -20 else "warning",
                        "current": round(curr_val, 4),
                        "previous": round(prev_val, 4),
                        "change_pct": round(change_pct, 2),
                        "message": f"{name} dropped by {abs(change_pct):.1f}% (from {prev_val:.3f} to {curr_val:.3f})",
                    })

        return {
            "alerts": alerts,
            "has_regressions": len(alerts) > 0,
            "current_run_id": current.id,
            "previous_run_id": previous.id,
        }
    finally:
        db.close()
