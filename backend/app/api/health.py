from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health Check")
async def health_check():
    """
    Returns API health status.
    """
    return {
        "status": "ok",
        "service": "travel-intelligence-backend"
    }
