from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.utils.validators import validate_password_strength

class UserRegister(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return validate_password_strength(v)

class EmailRequest(BaseModel):
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    username: str | None
    email: EmailStr
    name: str | None
    auth_method: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
    
class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_.-]+$", description="Username should only contain alphanumeric characters, _, ., and -")
    name: str | None = Field(default=None, min_length=3, max_length=20)
    gender: Literal['male', 'female'] | None
    age: int | None = Field(None, ge=1, le=120, description="Age must be between 1 and 120")
    weight: float | None = Field(None, ge=5, le=300, description="Weight must be between 5 and 300 kg")
    height: float | None = Field(None, ge=70, le=250, description="Height must be between 70 and 250 cm")

    
