from app.agents.research_agent import ResearchAgent
from app.agents.rag_agent import RAGAgent

research = ResearchAgent()
rag = RAGAgent()

research.research(
    "Vector Databases"
)

rag.ask(
    "What is Redis?"
)

print(
    research.memory.get_context()
)
