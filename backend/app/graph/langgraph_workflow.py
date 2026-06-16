"""
LangGraph workflow — main agent orchestration graph.

Flow:
  load_memory → router → [tool | rag | research | supervisor | brainstorm | graph_rag] → save_memory → END

Each node execution is traced with timing and success metrics.
"""

import time
import uuid
from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.rag_agent import RAGAgent
from app.agents.research_agent import ResearchAgent
from app.agents.tool_agent import ToolAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.brainstorm_agent import BrainstormAgent
from app.knowledge_graph.graph_rag import GraphRAGService
from app.graph.memory_node import load_memory_node
from app.graph.save_memory_node import save_memory_node
from app.evaluation.agent_evaluator import record_agent_execution


class GraphState(TypedDict):
    query: str
    result: str
    route: str
    session_id: Optional[str]
    sources: Optional[list]
    history: list
    trace_id: Optional[str]
    execution_trace: Optional[list]


tool_agent = ToolAgent()
rag_agent = RAGAgent()
research_agent = ResearchAgent()
supervisor_agent = SupervisorAgent()
brainstorm_agent = BrainstormAgent()


MATH_KEYWORDS = [
    "+", "-", "*", "/",
    "add", "subtract", "multiply", "divide",
    "previous result", "last result", "previous answer",
    "calculate", "compute", "times", "plus", "minus",
    "sum of", "product of", "divided by",
]

RAG_KEYWORDS = [
    "vector database", "rag", "enterprise ai",
    "langgraph", "pgvector", "redis memory",
    "document", "uploaded", "pdf", "file",
    "what does the document", "according to",
    "summarize", "summary", "overview",
    "main sections", "sections in", "key points",
    "what is this document", "what does it say",
    "list all", "list the sections",
    "mention", "mentioned in",
]

SUPERVISOR_KEYWORDS = [
    "plan", "execute", "complex task", "multi-step", "workflow", "orchestrate", "step by step"
]

BRAINSTORM_KEYWORDS = [
    "brainstorm", "ideas", "critique", "generate ideas", "strategy", "creative"
]

GRAPH_RAG_KEYWORDS = [
    "knowledge graph", "entity", "relationship", "connected to",
    "related to", "graph", "entities", "relationships",
]


def _trace_node(state: GraphState, node_name: str, duration_ms: float, success: bool):
    """Record a node execution in the trace."""
    trace_entry = {
        "node": node_name,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    trace = state.get("execution_trace") or []
    trace.append(trace_entry)
    return trace


def router_node(state: GraphState):
    """Decide which agent handles this query."""
    start = time.perf_counter()
    query = state["query"].lower()

    # Assign a trace_id if not present
    trace_id = state.get("trace_id") or str(uuid.uuid4())[:12]

    if any(kw in query for kw in SUPERVISOR_KEYWORDS):
        route = "supervisor"
    elif any(kw in query for kw in BRAINSTORM_KEYWORDS):
        route = "brainstorm"
    elif any(kw in query for kw in GRAPH_RAG_KEYWORDS):
        route = "graph_rag"
    elif any(kw in query for kw in MATH_KEYWORDS):
        route = "tool"
    elif any(kw in query for kw in RAG_KEYWORDS):
        route = "rag"
    else:
        route = "research"

    duration = (time.perf_counter() - start) * 1000
    trace = _trace_node(state, "router", duration, True)

    return {"route": route, "trace_id": trace_id, "execution_trace": trace}


def tool_node(state: GraphState):
    start = time.perf_counter()
    try:
        result = tool_agent.run(state["query"])
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="tool", query=state["query"],
            execution_time_ms=duration, success=True,
            result_length=len(result), session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "tool", duration, True)
        return {"result": result, "execution_trace": trace}
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="tool", query=state["query"],
            execution_time_ms=duration, success=False,
            session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "tool", duration, False)
        return {"result": f"Tool error: {e}", "execution_trace": trace}


def rag_node(state: GraphState):
    start = time.perf_counter()
    try:
        response = rag_agent.ask(state["query"])
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="rag", query=state["query"],
            execution_time_ms=duration, success=True,
            result_length=len(response["answer"]), session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "rag", duration, True)
        return {"result": response["answer"], "sources": response["sources"], "execution_trace": trace}
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="rag", query=state["query"],
            execution_time_ms=duration, success=False,
            session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "rag", duration, False)
        return {"result": f"RAG error: {e}", "execution_trace": trace}


def research_node(state: GraphState):
    start = time.perf_counter()
    try:
        result = research_agent.research(state["query"])
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="research", query=state["query"],
            execution_time_ms=duration, success=True,
            result_length=len(result), session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "research", duration, True)
        return {"result": result, "execution_trace": trace}
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="research", query=state["query"],
            execution_time_ms=duration, success=False,
            session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "research", duration, False)
        return {"result": f"Research error: {e}", "execution_trace": trace}


def supervisor_node(state: GraphState):
    start = time.perf_counter()
    try:
        result = supervisor_agent.execute_task(state["query"], session_id=state.get("session_id"))
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="supervisor", query=state["query"],
            execution_time_ms=duration, success=True,
            result_length=len(result), session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "supervisor", duration, True)
        return {"result": result, "execution_trace": trace}
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="supervisor", query=state["query"],
            execution_time_ms=duration, success=False,
            session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "supervisor", duration, False)
        return {"result": f"Supervisor error: {e}", "execution_trace": trace}


def brainstorm_node(state: GraphState):
    start = time.perf_counter()
    try:
        result = brainstorm_agent.brainstorm(state["query"])
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="brainstorm", query=state["query"],
            execution_time_ms=duration, success=True,
            result_length=len(result), session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "brainstorm", duration, True)
        return {"result": result, "execution_trace": trace}
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="brainstorm", query=state["query"],
            execution_time_ms=duration, success=False,
            session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "brainstorm", duration, False)
        return {"result": f"Brainstorm error: {e}", "execution_trace": trace}


def graph_rag_node(state: GraphState):
    start = time.perf_counter()
    try:
        service = GraphRAGService()
        response = service.query(state["query"])
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="graph_rag", query=state["query"],
            execution_time_ms=duration, success=True,
            result_length=len(response["answer"]), session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "graph_rag", duration, True)
        return {
            "result": response["answer"],
            "sources": response.get("sources", []),
            "execution_trace": trace,
        }
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        record_agent_execution(
            trace_id=state.get("trace_id", ""),
            route="graph_rag", query=state["query"],
            execution_time_ms=duration, success=False,
            session_id=state.get("session_id"),
        )
        trace = _trace_node(state, "graph_rag", duration, False)
        return {"result": f"GraphRAG error: {e}", "execution_trace": trace}


def route_decision(state: GraphState) -> str:
    return state["route"]


# build the graph
builder = StateGraph(GraphState)

builder.add_node("load_memory", load_memory_node)
builder.add_node("router", router_node)
builder.add_node("tool", tool_node)
builder.add_node("rag", rag_node)
builder.add_node("research", research_node)
builder.add_node("supervisor", supervisor_node)
builder.add_node("brainstorm", brainstorm_node)
builder.add_node("graph_rag", graph_rag_node)
builder.add_node("save_memory", save_memory_node)

builder.set_entry_point("load_memory")
builder.add_edge("load_memory", "router")

builder.add_conditional_edges(
    "router",
    route_decision,
    {
        "tool": "tool",
        "rag": "rag",
        "research": "research",
        "supervisor": "supervisor",
        "brainstorm": "brainstorm",
        "graph_rag": "graph_rag",
    },
)

builder.add_edge("tool", "save_memory")
builder.add_edge("rag", "save_memory")
builder.add_edge("research", "save_memory")
builder.add_edge("supervisor", "save_memory")
builder.add_edge("brainstorm", "save_memory")
builder.add_edge("graph_rag", "save_memory")
builder.add_edge("save_memory", END)

graph = builder.compile()
