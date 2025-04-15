from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    username: str | None = Field(None, max_length=40)
    email: EmailStr
    password: str | None = Field(None, min_length=8, max_length=255)
    name: str | None = Field(None, max_length=40)

class UserResponse(BaseModel):
    id: int
    username: str | None
    email: EmailStr
    name: str | None
    auth_method: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)