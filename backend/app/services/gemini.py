"""
Gemini AI Service Adapter (Backend Only).

Integrates with Google's official Gemini SDK.
Handles client initialization, connectivity verification, and generation tests.
The GEMINI_API_KEY is kept strictly server-side and is never exposed to clients.
"""

from typing import Any, Dict, Optional
from app.core.config import settings

_gemini_client: Optional[Any] = None


def get_gemini_client() -> Optional[Any]:
    """
    Initializes and returns the official Gemini client if GEMINI_API_KEY is configured.
    Returns None if the key is missing or initialization fails.
    """
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client

    if not settings.GEMINI_API_KEY:
        return None

    try:
        from google import genai
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return _gemini_client
    except Exception as e:
        print(f"[Gemini Service Warning] Failed to initialize Gemini Client: {e}")
        return None


def get_gemini_status() -> Dict[str, Any]:
    """
    Returns provider configuration status and model name without exposing any keys.
    """
    has_key = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your-gemini-api-key-here")
    return {
        "configured": has_key,
        "provider": "gemini",
        "model": settings.GEMINI_MODEL,
        "status": "ready" if has_key else "key_required"
    }


async def test_gemini_generation(prompt: str = "Hello from TravelIQ platform") -> Dict[str, Any]:
    """
    Lightweight test function to verify end-to-end Gemini connectivity.
    Safe helper for developer connectivity verification.
    """
    client = get_gemini_client()
    if not client:
        return {
            "success": False,
            "message": "Gemini API key is not configured in backend/.env",
            "provider": "gemini",
            "model": settings.GEMINI_MODEL
        }

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        return {
            "success": True,
            "provider": "gemini",
            "model": settings.GEMINI_MODEL,
            "response_text": getattr(response, "text", "")
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Gemini generation error: {str(e)}",
            "provider": "gemini",
            "model": settings.GEMINI_MODEL
        }
