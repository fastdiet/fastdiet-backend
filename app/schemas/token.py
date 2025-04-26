from pydantic import BaseModel

class TokenResponse(BaseModel):
    access_token: str | None
    refresh_token: str | None
    token_type: str | None
