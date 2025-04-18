from pydantic import BaseModel, EmailStr


class ResetCodeVerification(BaseModel):
    email: EmailStr
    code: str

class PasswordReset(BaseModel):
    email: EmailStr
    code: str
    new_password: str