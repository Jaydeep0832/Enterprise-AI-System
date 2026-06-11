from app.agents.base_agent import BaseAgent
from app.tools.registry import ToolRegistry

class ResearchAgent(BaseAgent):
    
    def __init__(self):
        super().__init__()
        self.registry = ToolRegistry()

    def research(self, topic: str) -> str:
        web_search = self.registry.get_tool("web_search")
        search_results = ""
        
        if web_search:
            search_results = web_search.execute(topic)
            
        prompt = f"""You are an expert Research Agent. Explain the following topic in detail.
        
Use the following recent web search results to inform your answer:
{search_results}

Topic: {topic}

Include:
- Definition
- Key concepts
- Real-world applications
- Recent developments (based on web results)"""

        return self.run(prompt)
