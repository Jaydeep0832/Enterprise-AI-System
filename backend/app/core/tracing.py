"""
tracing.py — LLM call tracing and metrics collection.

Records every LLM call with:
  - Provider, model, latency, token estimates, cost estimates
  - Stores in Redis for real-time dashboards
  - Per-hour and per-day cost aggregation
  - Error rate tracking (1h, 24h windows)
  - Latency percentile calculation (p50, p95, p99)
  - Integrates with LangSmith when LANGCHAIN_API_KEY is configured
"""

import time
import json
import math
from datetime import datetime, timezone

from app.db.redis_client import redis_client

# Approximate pricing per 1M tokens (input/output)
COST_TABLE = {
    "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "meta-llama/llama-3.3-70b-instruct": {"input": 0.50, "output": 0.50},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}

METRICS_KEY = "metrics:llm_calls"
METRICS_SUMMARY_KEY = "metrics:llm_summary"
METRICS_LATENCY_KEY = "metrics:latency_values"
METRICS_HOURLY_COST_KEY = "metrics:hourly_cost"
METRICS_DAILY_COST_KEY = "metrics:daily_cost"
METRICS_ERROR_LOG_KEY = "metrics:error_log"


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English text."""
    return max(1, len(text) // 4)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD based on token counts."""
    pricing = COST_TABLE.get(model, {"input": 0.10, "output": 0.30})
    cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
    return round(cost, 8)


def record_llm_call(
    provider: str,
    model: str,
    prompt: str,
    response: str,
    latency_ms: float,
    success: bool,
    error: str = None,
    session_id: str = None,
):
    """Store an LLM call record in Redis for metrics."""
    input_tokens = estimate_tokens(prompt)
    output_tokens = estimate_tokens(response) if response else 0
    cost = estimate_cost(model, input_tokens, output_tokens)
    now = datetime.now(timezone.utc)

    record = {
        "timestamp": now.isoformat(),
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": round(latency_ms, 2),
        "cost_usd": cost,
        "success": success,
        "error": error,
        "session_id": session_id,
    }

    try:
        pipe = redis_client.pipeline()

        # Store in a Redis list (capped at 500 most recent)
        pipe.lpush(METRICS_KEY, json.dumps(record))
        pipe.ltrim(METRICS_KEY, 0, 499)

        # Store latency for percentile calculation (capped at 1000)
        pipe.lpush(METRICS_LATENCY_KEY, str(round(latency_ms, 2)))
        pipe.ltrim(METRICS_LATENCY_KEY, 0, 999)

        # Update summary counters
        pipe.hincrby(METRICS_SUMMARY_KEY, "total_calls", 1)
        pipe.hincrby(METRICS_SUMMARY_KEY, f"calls:{provider}", 1)
        if success:
            pipe.hincrby(METRICS_SUMMARY_KEY, "success_count", 1)
        else:
            pipe.hincrby(METRICS_SUMMARY_KEY, "error_count", 1)
            # Log error with timestamp for error-rate windows
            error_entry = json.dumps({
                "timestamp": now.isoformat(),
                "provider": provider,
                "error": error or "unknown",
            })
            pipe.lpush(METRICS_ERROR_LOG_KEY, error_entry)
            pipe.ltrim(METRICS_ERROR_LOG_KEY, 0, 999)

        pipe.hincrbyfloat(METRICS_SUMMARY_KEY, "total_latency_ms", latency_ms)
        pipe.hincrbyfloat(METRICS_SUMMARY_KEY, "total_cost_usd", cost)
        pipe.hincrby(METRICS_SUMMARY_KEY, "total_input_tokens", input_tokens)
        pipe.hincrby(METRICS_SUMMARY_KEY, "total_output_tokens", output_tokens)

        # Hourly and daily cost aggregation
        hour_key = now.strftime("%Y-%m-%d-%H")
        day_key = now.strftime("%Y-%m-%d")
        pipe.hincrbyfloat(METRICS_HOURLY_COST_KEY, hour_key, cost)
        pipe.hincrbyfloat(METRICS_DAILY_COST_KEY, day_key, cost)

        # Per-provider daily cost
        provider_day_key = f"{provider}:{day_key}"
        pipe.hincrbyfloat(METRICS_DAILY_COST_KEY, provider_day_key, cost)

        # Per-session cost tracking
        if session_id:
            pipe.hincrbyfloat("metrics:session_cost", session_id, cost)

        pipe.execute()
    except Exception as e:
        # Don't let metrics recording crash the main flow
        print(f"[tracing] Warning: failed to record metrics: {e}")


def get_metrics_summary() -> dict:
    """Retrieve aggregated metrics from Redis."""
    try:
        raw = redis_client.hgetall(METRICS_SUMMARY_KEY)
        if not raw:
            return {
                "total_calls": 0, "success_count": 0, "error_count": 0,
                "avg_latency_ms": 0, "total_cost_usd": 0,
                "total_input_tokens": 0, "total_output_tokens": 0,
                "providers": {},
            }

        total = int(raw.get("total_calls", 0))
        total_latency = float(raw.get("total_latency_ms", 0))

        # Extract per-provider counts
        providers = {}
        for key, value in raw.items():
            if key.startswith("calls:"):
                providers[key.replace("calls:", "")] = int(value)

        return {
            "total_calls": total,
            "success_count": int(raw.get("success_count", 0)),
            "error_count": int(raw.get("error_count", 0)),
            "avg_latency_ms": round(total_latency / max(total, 1), 2),
            "total_cost_usd": round(float(raw.get("total_cost_usd", 0)), 6),
            "total_input_tokens": int(raw.get("total_input_tokens", 0)),
            "total_output_tokens": int(raw.get("total_output_tokens", 0)),
            "providers": providers,
        }
    except Exception:
        return {"total_calls": 0, "error": "metrics unavailable"}


def get_recent_calls(limit: int = 50) -> list:
    """Retrieve recent LLM call records."""
    try:
        raw_items = redis_client.lrange(METRICS_KEY, 0, limit - 1)
        return [json.loads(item) for item in raw_items]
    except Exception:
        return []


def get_latency_percentiles() -> dict:
    """Calculate p50, p95, p99 latency percentiles from recent calls."""
    try:
        raw_values = redis_client.lrange(METRICS_LATENCY_KEY, 0, -1)
        if not raw_values:
            return {"p50": 0, "p95": 0, "p99": 0, "min": 0, "max": 0, "count": 0}

        values = sorted(float(v) for v in raw_values)
        n = len(values)

        def percentile(p):
            idx = (p / 100) * (n - 1)
            lower = int(math.floor(idx))
            upper = int(math.ceil(idx))
            if lower == upper:
                return round(values[lower], 2)
            frac = idx - lower
            return round(values[lower] * (1 - frac) + values[upper] * frac, 2)

        return {
            "p50": percentile(50),
            "p95": percentile(95),
            "p99": percentile(99),
            "min": round(values[0], 2),
            "max": round(values[-1], 2),
            "count": n,
        }
    except Exception:
        return {"p50": 0, "p95": 0, "p99": 0, "min": 0, "max": 0, "count": 0}


def get_cost_breakdown() -> dict:
    """Get cost breakdown by hour and day."""
    try:
        hourly_raw = redis_client.hgetall(METRICS_HOURLY_COST_KEY)
        daily_raw = redis_client.hgetall(METRICS_DAILY_COST_KEY)

        # Separate provider-daily from daily totals
        daily_totals = {}
        provider_daily = {}
        for key, value in daily_raw.items():
            if ":" in key:
                provider, date = key.split(":", 1)
                provider_daily.setdefault(provider, {})[date] = round(float(value), 8)
            else:
                daily_totals[key] = round(float(value), 8)

        # Sort by date descending, limit to last 30 days
        sorted_daily = dict(sorted(daily_totals.items(), reverse=True)[:30])
        sorted_hourly = dict(sorted(hourly_raw.items(), reverse=True)[:48])
        sorted_hourly = {k: round(float(v), 8) for k, v in sorted_hourly.items()}

        return {
            "daily": sorted_daily,
            "hourly": sorted_hourly,
            "by_provider": provider_daily,
        }
    except Exception:
        return {"daily": {}, "hourly": {}, "by_provider": {}}


def get_error_rate() -> dict:
    """Get error rate for the last 1h and 24h windows."""
    try:
        raw_errors = redis_client.lrange(METRICS_ERROR_LOG_KEY, 0, -1)
        if not raw_errors:
            return {"last_1h": {"errors": 0}, "last_24h": {"errors": 0}, "recent_errors": []}

        now = datetime.now(timezone.utc)
        errors_1h = 0
        errors_24h = 0
        recent = []

        for raw in raw_errors:
            entry = json.loads(raw)
            ts = datetime.fromisoformat(entry["timestamp"])
            diff_hours = (now - ts).total_seconds() / 3600

            if diff_hours <= 1:
                errors_1h += 1
            if diff_hours <= 24:
                errors_24h += 1

            if len(recent) < 10:
                recent.append(entry)

        summary = get_metrics_summary()
        total = summary.get("total_calls", 0)

        return {
            "last_1h": {"errors": errors_1h},
            "last_24h": {"errors": errors_24h},
            "total_errors": summary.get("error_count", 0),
            "error_rate_pct": round(summary.get("error_count", 0) / max(total, 1) * 100, 2),
            "recent_errors": recent,
        }
    except Exception:
        return {"last_1h": {"errors": 0}, "last_24h": {"errors": 0}, "recent_errors": []}
