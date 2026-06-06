from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from app.agents.tool_agent import ToolAgent
from app.agents.rag_agent import RAGAgent
from app.agents.research_agent import ResearchAgent
from app.graph.memory_node import load_memory_node
from app.graph.save_memory_node import save_memory_node


class GraphState(TypedDict):
    query: str
    result: str
    route: str
    session_id: Optional[str]
    history: list


tool_agent = ToolAgent()
rag_agent = RAGAgent()
research_agent = ResearchAgent()


MATH_KEYWORDS = [
    "+", "-", "*", "/",
    "add", "subtract", "multiply", "divide",
    "previous result", "last result", "previous answer",
]

RAG_KEYWORDS = [
    "vector database", "rag", "enterprise ai",
    "langgraph", "pgvector", "redis memory",
    "document", "uploaded",
]


def router_node(state: GraphState):
    query = state["query"].lower()

    if any(kw in query for kw in MATH_KEYWORDS):
        return {"route": "tool"}

    if any(kw in query for kw in RAG_KEYWORDS):
        return {"route": "rag"}

    return {"route": "research"}


def tool_node(state: GraphState):
    result = tool_agent.run(state["query"])
    return {"result": result}


def rag_node(state: GraphState):
    result = rag_agent.ask(state["query"])
    return {"result": result}


def research_node(state: GraphState):
    result = research_agent.research(state["query"])
    return {"result": result}


def route_decision(state):
    return state["route"]


# build the graph
builder = StateGraph(GraphState)

builder.add_node("load_memory", load_memory_node)
builder.add_node("router", router_node)
builder.add_node("tool", tool_node)
builder.add_node("rag", rag_node)
builder.add_node("research", research_node)
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
    },
)

builder.add_edge("tool", "save_memory")
builder.add_edge("rag", "save_memory")
builder.add_edge("research", "save_memory")
builder.add_edge("save_memory", END)

graph = builder.compile()
