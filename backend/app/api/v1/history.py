from fastapi import APIRouter

from app.memory.conversation_memory import memory

router = APIRouter()


@router.get("/history")
def get_history():

    return {
        "messages": memory.get_context()
    }

@router.get("/history/count")
def history_count():

    return {
        "count": len(memory.get_context())
    }
