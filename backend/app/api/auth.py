from fastapi import APIRouter, Depends
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.user import CurrentUserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me", response_model=CurrentUserResponse, summary="Get Current Authenticated User")
async def get_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Returns the authenticated user extracted from the verified Supabase JWT Bearer token.
    """
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_authenticated=True
    )
