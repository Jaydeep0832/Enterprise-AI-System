from app.agents.tool_agent import ToolAgent
from app.agents.rag_agent import RAGAgent
from app.agents.research_agent import ResearchAgent


class RouterAgent:

    def __init__(self):
        self.tool_agent = ToolAgent()
        self.rag_agent = RAGAgent()
        self.research_agent = ResearchAgent()

    def route(self, query: str):
        query_lower = query.lower()

        math_keywords = [
            "+", "-", "*", "/",
            "add", "subtract", "multiply", "divide",
            "previous result", "last result", "previous answer",
        ]

        if any(kw in query_lower for kw in math_keywords):
            return self.tool_agent.run(query)

        rag_keywords = [
            "vector database", "rag", "enterprise ai",
            "langgraph", "pgvector", "redis memory",
        ]

        if any(kw in query_lower for kw in rag_keywords):
            return self.rag_agent.ask(query)

        return self.research_agent.research(query)
