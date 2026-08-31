"""
Auth Pydantic schemas — re-exports for clean package organization.

Supabase Auth handles all authentication. These schemas define the
response shape when the backend returns the authenticated user's identity.
"""

from app.schemas.user import CurrentUserResponse, UserProfileResponse

__all__ = ["CurrentUserResponse", "UserProfileResponse"]
