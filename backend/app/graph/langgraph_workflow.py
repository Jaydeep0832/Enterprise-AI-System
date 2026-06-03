from typing import TypedDict

from langgraph.graph import StateGraph
from langgraph.graph import END

from app.agents.tool_agent import ToolAgent
from app.agents.rag_agent import RAGAgent
from app.agents.research_agent import ResearchAgent


class GraphState(TypedDict):
    query: str
    result: str
    route: str


tool_agent = ToolAgent()
rag_agent = RAGAgent()
research_agent = ResearchAgent()


def router_node(state: GraphState):

    query = state["query"].lower()

    math_keywords = [
        "+",
        "-",
        "*",
        "/",
        "add",
        "subtract",
        "multiply",
        "divide",
        "previous result",
        "last result",
        "previous answer"
    ]

    if any(
        keyword in query
        for keyword in math_keywords
    ):
        print("ROUTER -> TOOL")

        return {
            "route": "tool"
        }

    rag_keywords = [
        "vector database",
        "rag",
        "enterprise ai",
        "langgraph",
        "pgvector",
        "redis memory"
    ]

    if any(
        keyword in query
        for keyword in rag_keywords
    ):
        return {
            "route": "rag"
        }
    print("ROUTER -> RESEARCH")
    return {
        "route": "research"
    }

def tool_node(state: GraphState):
    print("TOOL NODE EXECUTED")
    return {
        "result": tool_agent.run(
            state["query"]
        )
    }


def rag_node(state: GraphState):

    return {
        "result": rag_agent.ask(
            state["query"]
        )
    }


def research_node(state: GraphState):

    return {
        "result": research_agent.research(
            state["query"]
        )
    }


builder = StateGraph(GraphState)

builder.add_node("router", router_node)
builder.add_node("tool", tool_node)
builder.add_node("rag", rag_node)
builder.add_node("research", research_node)

builder.set_entry_point("router")


def route_decision(state):

    return state["route"]


builder.add_conditional_edges(
    "router",
    route_decision,
    {
        "tool": "tool",
        "rag": "rag",
        "research": "research"
    }
)

builder.add_edge("tool", END)
builder.add_edge("rag", END)
builder.add_edge("research", END)

graph = builder.compile()
