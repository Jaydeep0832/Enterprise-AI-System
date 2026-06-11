import json
import re
from app.agents.base_agent import BaseAgent

class BrainstormAgent(BaseAgent):
    """
    Implements a multi-step brainstorming protocol:
    1. Generator: Generates initial ideas.
    2. Critic: Evaluates the ideas.
    3. Synthesizer: Refines ideas based on critique.
    """

    def generate_ideas(self, topic: str, count: int = 3) -> str:
        prompt = f"""You are an Idea Generator. Generate {count} distinct, creative ideas for the following topic: {topic}.
        Format your response as a numbered list."""
        return self.run(prompt)

    def critique_ideas(self, topic: str, ideas: str) -> str:
        prompt = f"""You are an expert Critic. Review the following ideas for the topic '{topic}'.
        Identify the strengths and weaknesses of each idea, and point out any feasibility issues.
        
        Ideas:
        {ideas}
        
        Critique:"""
        return self.run(prompt)

    def synthesize(self, topic: str, ideas: str, critique: str) -> str:
        prompt = f"""You are a Decision Synthesizer. Based on the initial ideas and the critique, 
        formulate a single, refined, and highly actionable strategy for the topic '{topic}'.
        
        Initial Ideas:
        {ideas}
        
        Critique:
        {critique}
        
        Refined Strategy:"""
        return self.run(prompt)

    def brainstorm(self, topic: str) -> str:
        # Full end-to-end brainstorming workflow
        ideas = self.generate_ideas(topic)
        critique = self.critique_ideas(topic, ideas)
        final_strategy = self.synthesize(topic, ideas, critique)
        
        return f"### Initial Ideas\n{ideas}\n\n### Critique\n{critique}\n\n### Final Strategy\n{final_strategy}"
