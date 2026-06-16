"""
agent_evaluator.py — Agent execution evaluation.

Evaluates:
  1. Routing accuracy — did the router pick the right agent?
  2. Tool use efficiency — number of tool calls vs. task complexity
  3. Task completion rate — did the agent complete the task?
  4. Execution time tracking per agent type
"""

import json
from datetime import datetime, timezone

from app.db.redis_client import redis_client

AGENT_METRICS_KEY = "metrics:agent_execution"
AGENT_TRACE_KEY = "metrics:agent_traces"


def record_agent_execution(
    trace_id: str,
    route: str,
    query: str,
    execution_time_ms: float,
    success: bool,
    result_length: int = 0,
    session_id: str = None,
):
    """Record an agent execution for tracking and evaluation."""
    record = {
        "trace_id": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "route": route,
        "query_preview": query[:200],
        "execution_time_ms": round(execution_time_ms, 2),
        "success": success,
        "result_length": result_length,
        "session_id": session_id,
    }

    try:
        pipe = redis_client.pipeline()

        # Store trace
        pipe.lpush(AGENT_TRACE_KEY, json.dumps(record))
        pipe.ltrim(AGENT_TRACE_KEY, 0, 499)

        # Update per-agent counters
        pipe.hincrby(AGENT_METRICS_KEY, f"calls:{route}", 1)
        if success:
            pipe.hincrby(AGENT_METRICS_KEY, f"success:{route}", 1)
        else:
            pipe.hincrby(AGENT_METRICS_KEY, f"errors:{route}", 1)
        pipe.hincrbyfloat(AGENT_METRICS_KEY, f"latency:{route}", execution_time_ms)

        pipe.execute()
    except Exception as e:
        print(f"[agent_evaluator] Warning: failed to record: {e}")


def get_agent_metrics() -> dict:
    """Get per-agent execution metrics."""
    try:
        raw = redis_client.hgetall(AGENT_METRICS_KEY)
        if not raw:
            return {"agents": {}}

        agents = {}
        for key, value in raw.items():
            metric_type, agent_name = key.split(":", 1)
            if agent_name not in agents:
                agents[agent_name] = {"calls": 0, "success": 0, "errors": 0, "avg_latency_ms": 0}

            if metric_type == "calls":
                agents[agent_name]["calls"] = int(value)
            elif metric_type == "success":
                agents[agent_name]["success"] = int(value)
            elif metric_type == "errors":
                agents[agent_name]["errors"] = int(value)
            elif metric_type == "latency":
                agents[agent_name]["total_latency"] = float(value)

        # Calculate averages and success rates
        for name, data in agents.items():
            total = data["calls"]
            data["avg_latency_ms"] = round(data.pop("total_latency", 0) / max(total, 1), 2)
            data["success_rate_pct"] = round(data["success"] / max(total, 1) * 100, 1)

        return {"agents": agents}
    except Exception:
        return {"agents": {}}


def get_recent_traces(limit: int = 50) -> list:
    """Get recent agent execution traces."""
    try:
        raw = redis_client.lrange(AGENT_TRACE_KEY, 0, limit - 1)
        return [json.loads(item) for item in raw]
    except Exception:
        return []
