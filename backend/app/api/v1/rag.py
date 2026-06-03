from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.rag_agent import RAGAgent

router = APIRouter()

agent = RAGAgent()


class RAGRequest(BaseModel):
    question: str


@router.post("/rag")
async def rag(request: RAGRequest):
    answer = agent.ask(
        request.question
    )

    return {
        "answer": answer
    }
