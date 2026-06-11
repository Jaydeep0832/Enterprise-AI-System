"""
LangGraph workflow — main agent orchestration graph.

Flow:
  load_memory → router → [tool | rag | research | supervisor | brainstorm] → save_memory → END
"""

from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.rag_agent import RAGAgent
from app.agents.research_agent import ResearchAgent
from app.agents.tool_agent import ToolAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.brainstorm_agent import BrainstormAgent
from app.graph.memory_node import load_memory_node
from app.graph.save_memory_node import save_memory_node


class GraphState(TypedDict):
    query: str
    result: str
    route: str
    session_id: Optional[str]
    sources: Optional[list]
    history: list


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

def router_node(state: GraphState):
    """Decide which agent handles this query."""
    query = state["query"].lower()

    if any(kw in query for kw in SUPERVISOR_KEYWORDS):
        return {"route": "supervisor"}
        
    if any(kw in query for kw in BRAINSTORM_KEYWORDS):
        return {"route": "brainstorm"}

    if any(kw in query for kw in MATH_KEYWORDS):
        return {"route": "tool"}

    if any(kw in query for kw in RAG_KEYWORDS):
        return {"route": "rag"}

    return {"route": "research"}


def tool_node(state: GraphState):
    result = tool_agent.run(state["query"])
    return {"result": result}


def rag_node(state: GraphState):
    response = rag_agent.ask(state["query"])
    return {"result": response["answer"], "sources": response["sources"]}


def research_node(state: GraphState):
    result = research_agent.research(state["query"])
    return {"result": result}

def supervisor_node(state: GraphState):
    result = supervisor_agent.execute_task(state["query"], session_id=state.get("session_id"))
    return {"result": result}
    
def brainstorm_node(state: GraphState):
    result = brainstorm_agent.brainstorm(state["query"])
    return {"result": result}

def route_decision(state: GraphState) -> str:
    return state["route"]


from langgraph.checkpoint.memory import MemorySaver

# build the graph
builder = StateGraph(GraphState)

builder.add_node("load_memory", load_memory_node)
builder.add_node("router", router_node)
builder.add_node("tool", tool_node)
builder.add_node("rag", rag_node)
builder.add_node("research", research_node)
builder.add_node("supervisor", supervisor_node)
builder.add_node("brainstorm", brainstorm_node)
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
    },
)

builder.add_edge("tool", "save_memory")
builder.add_edge("rag", "save_memory")
builder.add_edge("research", "save_memory")
builder.add_edge("supervisor", "save_memory")
builder.add_edge("brainstorm", "save_memory")
builder.add_edge("save_memory", END)

# Configure Human-in-the-loop (HITL) by interrupting before high-risk nodes like tools
memory_saver = MemorySaver()
graph = builder.compile(checkpointer=memory_saver, interrupt_before=["tool"])
