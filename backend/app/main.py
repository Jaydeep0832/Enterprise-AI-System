"""
Enterprise AI System — FastAPI main entry point.

Registers all API routes, middleware, and startup events.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import setup_logger
from app.core.middleware import RequestTimingMiddleware

# Import all models so SQLAlchemy knows about them
from app.models.document import Base
from app.models import user, feedback, knowledge_graph, evaluation  # noqa: F401
from app.db.session import engine

# API routers
from app.api.v1.chat import router as chat_router
from app.api.v1.upload import router as upload_router
from app.api.v1.history import router as history_router
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.evaluation import router as eval_router
from app.api.v1.knowledge_graph import router as kg_router

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Create tables for new models (users, feedback, kg_nodes, kg_edges)
    Base.metadata.create_all(bind=engine)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    logger.info("👋 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS — configurable origins instead of wildcard
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
app.add_middleware(RequestTimingMiddleware)

# Register all API routers under /api/v1
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
app.include_router(upload_router, prefix="/api/v1", tags=["Upload"])
app.include_router(history_router, prefix="/api/v1", tags=["History"])
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(metrics_router, prefix="/api/v1", tags=["Metrics"])
app.include_router(feedback_router, prefix="/api/v1", tags=["Feedback"])
app.include_router(eval_router, prefix="/api/v1", tags=["Evaluation"])
app.include_router(kg_router, prefix="/api/v1", tags=["Knowledge Graph"])


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Enterprise AI System Running"}
