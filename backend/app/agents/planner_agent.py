import json
import re
from typing import List, Dict, Any

from app.agents.base_agent import BaseAgent
from app.tools.registry import ToolRegistry


class PlannerAgent(BaseAgent):
    """
    Decomposes complex tasks into manageable steps.
    """

    def __init__(self):
        super().__init__()
        self.registry = ToolRegistry()

    def plan(self, task: str) -> List[Dict[str, Any]]:
        tools_list = ", ".join(self.registry.list_tools())
        
        prompt = f"""
        You are an expert AI Planner. Break down the following task into a sequence of executable steps.
        You have access to these tools: {tools_list}.
        
        Return ONLY valid JSON in the following format:
        [
            {{"step_number": 1, "action": "tool_name_or_agent", "instruction": "detailed instruction"}},
            {{"step_number": 2, "action": "tool_name_or_agent", "instruction": "detailed instruction"}}
        ]
        
        Task: {task}
        """
        
        response = self.llm.generate(prompt)
        
        # Extract JSON from response
        try:
            # find JSON array block
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                return [{"step_number": 1, "action": "research", "instruction": task}]
        except Exception as e:
            return [{"step_number": 1, "action": "error", "instruction": f"Failed to parse plan: {e}"}]
