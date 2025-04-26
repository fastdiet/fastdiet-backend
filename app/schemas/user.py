from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.utils.validators import validate_password_strength

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str
    name: str | None = Field(None, max_length=40)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return validate_password_strength(v)

class UserResponse(BaseModel):
    id: int
    username: str | None
    email: EmailStr
    name: str | None
    auth_method: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
    