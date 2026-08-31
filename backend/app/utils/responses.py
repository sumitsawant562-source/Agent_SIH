"""
Standardized API error responses.

Provides helper functions that raise HTTPException with consistent
structure. Keeps error formatting uniform across all endpoints and
prevents accidental exposure of stack traces or secrets.
"""

from typing import Any, Optional
from fastapi import HTTPException, status


def not_found(resource: str = "Resource", identifier: Any = None) -> HTTPException:
    """Raise a 404 Not Found error."""
    detail = f"{resource} not found."
    if identifier is not None:
        detail = f"{resource} with ID '{identifier}' was not found."
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def forbidden(message: str = "You do not have permission to access this resource.") -> HTTPException:
    """Raise a 403 Forbidden error."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


def bad_request(message: str = "Invalid request data.") -> HTTPException:
    """Raise a 400 Bad Request error."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def unauthorized(message: str = "Authentication required.") -> HTTPException:
    """Raise a 401 Unauthorized error."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def internal_error(
    message: str = "An unexpected error occurred. Please try again later.",
    log_detail: Optional[str] = None,
) -> HTTPException:
    """
    Raise a 500 Internal Server Error.

    ``log_detail`` is printed server-side but NEVER exposed in the response.
    """
    if log_detail:
        print(f"[Internal Error] {log_detail}")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)


def error_response(status_code: int, message: str) -> dict:
    """Return a JSON-serializable error body (for non-exception use cases)."""
    return {"error": True, "status_code": status_code, "message": message}
