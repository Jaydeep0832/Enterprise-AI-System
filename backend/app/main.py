from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import setup_logger
from app.api.v1.health import router as health_router
from app.api.v1.chat import router as chat_router
from app.api.v1.rag import router as rag_router
from app.api.v1.research import router as research_router
from app.api.v1.history import router as history_router
from app.api.v1.upload import router as upload_router

logger = setup_logger()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

# register routes
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
app.include_router(rag_router, prefix="/api/v1", tags=["RAG"])
app.include_router(research_router, prefix="/api/v1", tags=["Research"])
app.include_router(history_router, prefix="/api/v1", tags=["History"])
app.include_router(upload_router, prefix="/api/v1", tags=["Upload"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Enterprise AI System Running"}
