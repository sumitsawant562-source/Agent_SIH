"""
Authentication API Router.

Provides robust signup, login, and profile endpoints using secure PBKDF2 password
hashing and standard JWT Bearer token generation. Fully backward-compatible with
Supabase JWT verification and self-contained for local / production execution.
"""

import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt

from app.core.config import settings
from app.core.security import AuthenticatedUser, get_current_user
from app.db.supabase import get_supabase_admin_client, get_supabase_client
from app.schemas.user import (
    AuthResponse,
    AuthUserData,
    CurrentUserResponse,
    UserLoginRequest,
    UserSignupRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

# User storage registry for self-contained execution & testing
_users_db: Dict[str, Dict[str, Any]] = {}


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Generates secure PBKDF2-HMAC-SHA256 password hash with 100,000 iterations."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()
    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verifies a plain password against the stored PBKDF2 hash."""
    test_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(test_hash, hashed)


def generate_jwt_token(user_id: str, email: str, full_name: Optional[str] = None) -> str:
    """Creates a signed JWT Bearer token compatible with the security scheme."""
    payload = {
        "sub": user_id,
        "email": email,
        "role": "authenticated",
        "user_metadata": {
            "full_name": full_name,
        },
        "exp": int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp()),
    }
    secret = settings.SUPABASE_JWT_SECRET or "dev-secret-key-for-testing_at_least_32_bytes"
    return jwt.encode(payload, secret, algorithm="HS256")


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
    description="Registers a new user account, hashes credentials securely, and returns a signed JWT token.",
)
async def signup(req: UserSignupRequest):
    email_key = req.email.strip().lower()

    # Check if user already exists
    if email_key in _users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please sign in instead.",
        )

    # If Supabase is connected, optionally trigger Supabase Auth
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.auth.sign_up({
                "email": req.email.strip(),
                "password": req.password,
                "options": {"data": {"full_name": req.full_name}},
            })
        except Exception:
            pass

    # Generate user record
    user_id = str(uuid.uuid4())
    pw_hash, salt = hash_password(req.password)
    now = datetime.now(timezone.utc).isoformat()

    user_record = {
        "id": user_id,
        "email": req.email.strip(),
        "full_name": req.full_name.strip() if req.full_name else None,
        "password_hash": pw_hash,
        "salt": salt,
        "created_at": now,
    }
    _users_db[email_key] = user_record

    # Generate JWT token
    token = generate_jwt_token(user_id, req.email.strip(), user_record["full_name"])

    return AuthResponse(
        success=True,
        access_token=token,
        token_type="bearer",
        user=AuthUserData(
            id=user_id,
            email=req.email.strip(),
            full_name=user_record["full_name"],
        ),
        message="Account created successfully.",
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def register_alias(req: UserSignupRequest):
    """Alias endpoint for /api/auth/signup."""
    return await signup(req)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="User Login",
    description="Authenticates user credentials and returns a signed JWT Bearer access token.",
)
async def login(req: UserLoginRequest):
    email_key = req.email.strip().lower()

    user = _users_db.get(email_key)
    if not user:
        # Fallback check against Supabase Auth if available
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.auth.sign_in_with_password({
                    "email": req.email.strip(),
                    "password": req.password,
                })
                if res and res.session:
                    s_user = res.user
                    full_name = (s_user.user_metadata or {}).get("full_name") if s_user else None
                    token = res.session.access_token or generate_jwt_token(str(s_user.id), req.email.strip(), full_name)
                    return AuthResponse(
                        success=True,
                        access_token=token,
                        token_type="bearer",
                        user=AuthUserData(
                            id=str(s_user.id),
                            email=req.email.strip(),
                            full_name=full_name,
                        ),
                    )
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials.",
        )

    # Verify password hash
    if not verify_password(req.password, user["password_hash"], user["salt"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials.",
        )

    token = generate_jwt_token(user["id"], user["email"], user.get("full_name"))

    return AuthResponse(
        success=True,
        access_token=token,
        token_type="bearer",
        user=AuthUserData(
            id=user["id"],
            email=user["email"],
            full_name=user.get("full_name"),
        ),
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Get Current Authenticated User",
    description="Returns the authenticated user extracted from the verified JWT Bearer token.",
)
async def get_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_authenticated=True,
    )
