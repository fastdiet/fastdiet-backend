from pydantic import BaseModel, EmailStr

class EmailCode(BaseModel):
    email: EmailStr
    code: str