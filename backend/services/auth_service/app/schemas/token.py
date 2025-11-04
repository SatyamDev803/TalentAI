"""Token schemas for authentication."""

from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload schema."""

    sub: str  # user_id
    exp: int
    iat: int
    jti: str  # JWT ID for blacklist


class RefreshRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str
