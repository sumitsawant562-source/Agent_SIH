from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.gemini import get_gemini_status, test_gemini_generation

router = APIRouter(prefix="/ai", tags=["AI"])


class GeminiTestRequest(BaseModel):
    prompt: Optional[str] = Field("Hello from TravelIQ platform", max_length=500)


@router.get("/status", summary="Get Gemini AI Status")
async def gemini_status():
    """
    Returns the backend Gemini AI configuration and readiness status
    without leaking sensitive API keys.
    """
    return get_gemini_status()


@router.post("/test", summary="Test Gemini AI Generation")
async def gemini_test(request: Optional[GeminiTestRequest] = None):
    """
    Executes a test generation query against Gemini to verify connectivity.
    """
    prompt = request.prompt if request and request.prompt else "Hello from TravelIQ platform"
    return await test_gemini_generation(prompt)
