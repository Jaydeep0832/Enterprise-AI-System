from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: Optional[list] = []
    agent_route: Optional[str] = None
    route: Optional[str] = None
    execution_trace: Optional[list] = []

