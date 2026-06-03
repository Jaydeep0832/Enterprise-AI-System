from app.agents.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    def research(self, topic: str) -> str:
        prompt = f"""
        Explain the following topic in detail.

        Topic:
        {topic}

        Include:
        - Definition
        - Key concepts
        - Real-world applications
        """

        return self.run(prompt)
