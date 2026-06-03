from app.agents.tool_agent import ToolAgent
from app.agents.research_agent import ResearchAgent
from app.agents.rag_agent import RAGAgent


class Orchestrator:

    def __init__(self):

        self.tool_agent = ToolAgent()
        self.research_agent = ResearchAgent()
        self.rag_agent = RAGAgent()

    def run(self, query: str):

        if any(
            op in query
            for op in ["+", "-", "*", "/"]
        ):
            return self.tool_agent.run(query)

        if "what is" in query.lower():
            return self.rag_agent.ask(query)

        return self.research_agent.research(query)
