from app.agents.research_agent import ResearchAgent

agent = ResearchAgent()

response = agent.research(
    "Vector Databases"
)

print(response)
