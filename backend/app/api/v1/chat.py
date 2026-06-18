import asyncio
import uuid

from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.graph.langgraph_workflow import graph

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())

    # Run in thread to avoid blocking the async event loop
    result = await asyncio.to_thread(
        graph.invoke,
        {
            "query": request.question,
            "session_id": session_id,
        },
    )

    return ChatResponse(
        answer=result["result"],
        session_id=session_id,
        sources=result.get("sources", []),
        route=result.get("route", ""),
        execution_trace=result.get("execution_trace", []),
    )
