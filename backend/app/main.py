from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.trips import router as trips_router
from app.api.ai import router as ai_router
from app.api.agent import router as agent_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Scalable backend foundation for the Agentic AI Personalized Travel Intelligence Platform (SIH Project).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api prefix
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(trips_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(agent_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    """
    Root entry point offering basic API metadata and links to docs.
    """
    return {
        "project": settings.PROJECT_NAME,
        "service": "travel-intelligence-backend",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
