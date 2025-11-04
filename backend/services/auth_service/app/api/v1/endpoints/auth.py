from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.deps import get_current_active_user, get_current_user_for_refresh
from app.core.security import decode_token
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import LoginRequest, UserCreate
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """Register a new user.

    **Request Body:**
    - email: Valid email address
    - password: Min 8 characters
    - full_name: User's full name
    - role: User role (ADMIN, RECRUITER, HIRING_MANAGER, CANDIDATE)

    **Response:**
    - access_token: JWT access token (15 min expiry)
    - refresh_token: JWT refresh token (7 days expiry)
    - token_type: "bearer"

    **Errors:**
    - 400: Email already registered
    - 422: Invalid input data
    """
    try:
        user, tokens = await auth_service.register_user(user_data)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """Login with email and password.

    **Request Body:**
    - email: User email address
    - password: User password

    **Response:**
    - access_token: JWT access token (15 min expiry)
    - refresh_token: JWT refresh token (7 days expiry)
    - token_type: "bearer"

    **Errors:**
    - 401: Invalid credentials
    - 403: User account inactive
    """
    try:
        user, tokens = await auth_service.authenticate_user(
            email=credentials.email,
            password=credentials.password,
        )
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user_for_refresh),
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """Refresh access token using refresh token.

    **Authorization:**
    - Bearer <refresh_token> in Authorization header

    **Response:**
    - access_token: New JWT access token (15 min expiry)
    - refresh_token: New JWT refresh token (7 days expiry)
    - token_type: "bearer"

    **Errors:**
    - 401: Invalid or expired refresh token
    """
    try:
        tokens = await auth_service.refresh_access_token(current_user)
        return tokens
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token",
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_active_user),
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """Logout user by revoking tokens.

    **Authorization:**
    - Bearer <access_token> in Authorization header

    **Effects:**
    - Access token blacklisted (can't be used again)
    - All refresh tokens revoked (can't refresh)

    **Response:**
    - 204 No Content on success

    **Errors:**
    - 401: Invalid or expired token
    """
    try:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
            )

        # Extract token from header
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
            )

        token = parts[1]
        payload = decode_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        access_jti = payload.get("jti")
        refresh_jti = payload.get("jti")

        await auth_service.logout_user(current_user, access_jti, refresh_jti)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to logout",
        )
