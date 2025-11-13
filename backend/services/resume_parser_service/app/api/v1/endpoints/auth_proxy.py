"""Authentication proxy endpoints."""

from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import httpx

from app.core.config import settings

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response schema."""

    message: str
    user: dict


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, response: Response):
    """Login via Auth Service and set cookie.

    This proxies the login request to the Auth Service and forwards the cookie.
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            # Call Auth Service
            auth_response = await client.post(
                f"http://localhost:{settings.auth_service_port}/api/v1/auth/login",
                json=credentials.model_dump(),
            )

            if auth_response.status_code != 200:
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=auth_response.json().get("detail", "Login failed"),
                )

            # Extract and set cookie from auth service
            for cookie_header in auth_response.headers.get_list("set-cookie"):
                # Parse cookie
                if "access_token" in cookie_header:
                    # Extract cookie value and attributes
                    cookie_parts = cookie_header.split(";")
                    cookie_value = cookie_parts[0].split("=", 1)[1]

                    # Set cookie with proper attributes
                    response.set_cookie(
                        key="access_token",
                        value=cookie_value,
                        httponly=True,
                        samesite="lax",
                        max_age=1800,  # 30 minutes
                    )
                    break

            return auth_response.json()

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Auth service unavailable: {str(e)}",
            )


@router.post("/logout")
async def logout(response: Response):
    """Logout and clear cookie."""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(access_token: Optional[str] = Cookie(None)):
    """Get current user info from cookie."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    return {"access_token": access_token[:20] + "...", "status": "authenticated"}
