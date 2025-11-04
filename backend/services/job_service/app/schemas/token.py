from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int
    iat: int
    jti: str  # JWT ID for blacklist


class RefreshRequest(BaseModel):
    refresh_token: str
