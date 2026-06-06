from fastapi import APIRouter

from app.agents.research_agent import ResearchAgent
from app.schemas.research import ResearchRequest, ResearchResponse

router = APIRouter()

agent = ResearchAgent()


@router.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    result = agent.research(request.topic)
    return ResearchResponse(result=result)
