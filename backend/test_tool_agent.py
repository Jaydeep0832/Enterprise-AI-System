from app.agents.tool_agent import ToolAgent

agent = ToolAgent()

print(
    agent.run("10 + 25 * 2")
)

print(
    agent.run(
        "Explain vector databases"
    )
)
