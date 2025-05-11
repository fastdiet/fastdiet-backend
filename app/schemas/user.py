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
    username: str | None
    name: str | None
