from app.agents.base_agent import BaseAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.tool_agent import ToolAgent
from app.agents.research_agent import ResearchAgent
from app.agents.rag_agent import RAGAgent
from app.memory.redis_memory import RedisMemory

class SupervisorAgent(BaseAgent):
    """
    The main orchestrator. It receives a task, asks the planner for a plan,
    and then delegates steps to the appropriate agents.
    """

    def __init__(self):
        super().__init__()
        self.planner = PlannerAgent()
        self.tool_agent = ToolAgent()
        self.research_agent = ResearchAgent()
        self.rag_agent = RAGAgent()

    def execute_task(self, task: str, session_id: str = None) -> str:
        plan = self.planner.plan(task)
        
        execution_log = []
        for step in plan:
            action = step.get("action", "").lower()
            instruction = step.get("instruction", "")
            step_num = step.get("step_number", "?")
            
            execution_log.append(f"Step {step_num}: {action} - {instruction}")
            
            # Delegate to specialized agents
            if "calculator" in action or "tool" in action:
                result = self.tool_agent.run(instruction)
            elif "rag" in action or "document" in action:
                result = self.rag_agent.ask(instruction)
            elif "search" in action or "research" in action or "web" in action:
                result = self.research_agent.research(instruction)
            else:
                # Default fallback
                result = self.research_agent.research(instruction)
                
            execution_log.append(f"Result: {result}\n")
            
        # Synthesize final answer
        log_text = "\n".join(execution_log)
        synthesis_prompt = f"""
        You are a Supervisor Agent. Based on the following execution log of a task, 
        provide a final, comprehensive answer to the user's original task.
        
        Original Task: {task}
        
        Execution Log:
        {log_text}
        
        Final Answer:
        """
        
        final_answer = self.llm.generate(synthesis_prompt)
        
        # Save to Episodic Memory
        if session_id:
            memory = RedisMemory(session_id)
            memory.save_episode(task, final_answer)
            
        return final_answer
