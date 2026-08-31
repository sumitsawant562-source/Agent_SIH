from fastapi import APIRouter, Depends
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.user import CurrentUserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=CurrentUserResponse, summary="Get Current Authenticated User Profile")
async def get_current_user_profile(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Returns the authenticated user's profile information extracted securely from Supabase Auth context.
    Never exposes service-role credentials or passwords.
    """
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_authenticated=True
    )
