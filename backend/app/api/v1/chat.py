from fastapi import APIRouter

from app.schemas.chat import (
    ChatRequest,
    ChatResponse
)

from app.graph.langgraph_workflow import graph


router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest
):

    result = graph.invoke(
        {
            "query": request.query
        }
    )

    return ChatResponse(
        answer=result["result"]
    )
