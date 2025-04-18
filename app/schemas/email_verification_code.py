from pydantic import BaseModel, EmailStr

class EmailVerification(BaseModel):
    email: EmailStr
    code: str