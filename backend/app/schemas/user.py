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
