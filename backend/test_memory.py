from app.agents.research_agent import ResearchAgent

agent = ResearchAgent()

agent.research(
    "Vector Databases"
)

print(
    agent.memory.get_context()
)
