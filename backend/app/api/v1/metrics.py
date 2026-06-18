"""
Metrics API — system observability dashboard data.

Routes:
  GET /metrics           — Aggregated system metrics
  GET /metrics/calls     — Recent LLM call log
  GET /metrics/latency   — Latency percentile stats
  GET /metrics/cost      — Cost breakdown by time period and provider
  GET /metrics/errors    — Error rate and recent errors
"""

from fastapi import APIRouter

from app.core.tracing import (
    get_metrics_summary,
    get_recent_calls,
    get_latency_percentiles,
    get_cost_breakdown,
    get_error_rate,
)
from app.evaluation.agent_evaluator import get_agent_metrics, get_recent_traces
from app.db.redis_client import redis_client

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """Return aggregated system metrics for the dashboard."""
    summary = get_metrics_summary()

    # Add memory and system stats
    try:
        redis_info = redis_client.info("memory")
        summary["redis_memory_mb"] = round(redis_info.get("used_memory", 0) / 1024 / 1024, 2)
    except Exception:
        summary["redis_memory_mb"] = 0

    # Add latency percentiles inline
    summary["latency_percentiles"] = get_latency_percentiles()

    return summary


@router.get("/metrics/calls")
async def get_call_log(limit: int = 50):
    """Return recent LLM call records."""
    calls = get_recent_calls(limit=min(limit, 200))
    return {"calls": calls, "count": len(calls)}


@router.get("/metrics/latency")
async def get_latency_stats():
    """Return latency percentile statistics (p50, p95, p99)."""
    return get_latency_percentiles()


@router.get("/metrics/cost")
async def get_cost_stats():
    """Return cost breakdown by hour, day, and provider."""
    breakdown = get_cost_breakdown()
    summary = get_metrics_summary()
    breakdown["total_cost_usd"] = summary.get("total_cost_usd", 0)
    return breakdown


@router.get("/metrics/errors")
async def get_error_stats():
    """Return error rate for 1h and 24h windows, plus recent errors."""
    return get_error_rate()


@router.get("/metrics/agents")
async def get_agent_stats():
    """Return per-agent execution metrics (calls, success rate, avg latency)."""
    return get_agent_metrics()


@router.get("/metrics/agent-traces")
async def get_agent_trace_log(limit: int = 50):
    """Return recent agent execution traces."""
    traces = get_recent_traces(limit=min(limit, 200))
    return {"traces": traces, "count": len(traces)}
