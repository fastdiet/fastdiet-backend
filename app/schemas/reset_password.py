from pydantic import BaseModel, EmailStr, field_validator
from app.utils.validators import validate_password_strength

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        return validate_password_strength(v)