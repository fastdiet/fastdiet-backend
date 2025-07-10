from pydantic import BaseModel
from app.schemas.user import UserResponse
from app.schemas.user_preferences import UserPreferencesResponse

class TokenResponse(BaseModel):
    access_token: str | None
    refresh_token: str | None
    token_type: str | None

class AuthResponse(BaseModel):
    tokens:  TokenResponse
    user: UserResponse
    preferences: UserPreferencesResponse | None = None

class RefreshRequest(BaseModel):
    refresh_token: str
