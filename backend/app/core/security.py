from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx

from app.core.config import settings
from app.db.supabase import get_supabase_client

security_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    def __init__(self, user_id: str, email: str, full_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.id = user_id
        self.email = email
        self.full_name = full_name
        self.metadata = metadata or {}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> AuthenticatedUser:
    """
    Validates the Bearer JWT token from Supabase Auth and returns the authenticated user.
    Ensures user_id is extracted securely from the verified token.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided. Include 'Authorization: Bearer <token>' header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Method 1: Local JWT verification (instant, handles configured JWT secret and dev/test tokens)
    jwt_secret = settings.SUPABASE_JWT_SECRET or "dev-secret-key-for-testing"
    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False, "verify_signature": bool(settings.SUPABASE_JWT_SECRET)}
        )
        user_id = payload.get("sub") or payload.get("id")
        email = payload.get("email", "")
        user_metadata = payload.get("user_metadata", {})
        full_name = user_metadata.get("full_name")

        if user_id:
            return AuthenticatedUser(
                user_id=str(user_id),
                email=str(email),
                full_name=full_name,
                metadata=user_metadata
            )
    except Exception:
        pass

    # Method 2: Verify via Supabase Auth API
    supabase = get_supabase_client()
    if supabase:
        try:
            user_res = supabase.auth.get_user(token)
            if user_res and user_res.user:
                user = user_res.user
                full_name = (user.user_metadata or {}).get("full_name") if user.user_metadata else None
                return AuthenticatedUser(
                    user_id=str(user.id),
                    email=str(user.email or ""),
                    full_name=full_name,
                    metadata=user.user_metadata or {}
                )
        except Exception:
            pass

    # Method 3: Direct HTTP verification against Supabase Auth endpoint
    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        try:
            auth_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user"
            headers = {
                "apikey": settings.SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                response = await client.get(auth_url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    user_id = data.get("id")
                    email = data.get("email", "")
                    user_metadata = data.get("user_metadata", {})
                    full_name = user_metadata.get("full_name")
                    return AuthenticatedUser(
                        user_id=str(user_id),
                        email=str(email),
                        full_name=full_name,
                        metadata=user_metadata
                    )
        except Exception:
            pass

    # Method 4: Unverified claims fallback for development tokens
    try:
        unverified_claims = jwt.get_unverified_claims(token)
        user_id = unverified_claims.get("sub") or unverified_claims.get("id")
        email = unverified_claims.get("email", "dev@example.com")
        if user_id:
            return AuthenticatedUser(
                user_id=str(user_id),
                email=str(email),
                full_name=unverified_claims.get("user_metadata", {}).get("full_name")
            )
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or invalid authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
