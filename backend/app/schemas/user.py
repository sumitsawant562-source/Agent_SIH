from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserProfileBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=150)


class UserProfileResponse(UserProfileBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_authenticated: bool = True


class UserSignupRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid user email address")
    password: str = Field(..., min_length=6, description="Password with minimum 6 characters")
    full_name: Optional[str] = Field(None, max_length=150, description="Full name of traveler")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class AuthUserData(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None


class AuthResponse(BaseModel):
    success: bool = True
    access_token: str
    token_type: str = "bearer"
    user: AuthUserData
    message: Optional[str] = None

