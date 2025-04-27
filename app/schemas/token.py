from pydantic import BaseModel
from app.schemas.user import UserResponse

class TokenResponse(BaseModel):
    access_token: str | None
    refresh_token: str | None
    token_type: str | None

class AuthResponse(BaseModel):
    tokens:  TokenResponse
    user: UserResponse
