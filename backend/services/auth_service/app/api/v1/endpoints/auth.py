from common.logger import logger
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)

from app.core.security import create_tokens, decode_token
from app.schemas.token import Token
from app.schemas.user import LoginRequest, UserCreate
from app.services.auth_service import AuthService, get_auth_service


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    try:
        user, tokens = await auth_service.register_user(user_data)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login")
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    response: Response = None,
) -> dict:

    try:
        user, tokens = await auth_service.authenticate_user(
            login_data.email, login_data.password
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        max_age=900,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        max_age=604800,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )

    logger.info(f"User logged in: {user.email}")

    return {
        "message": "Login successful",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "company_id": str(user.company_id) if user.company_id else None,
        },
    }


@router.post("/logout")
async def logout(response: Response) -> dict:

    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")

    logger.info("User logged out")

    return {"message": "Logout successful"}


# Refresh access token using refresh token from cookie
@router.post("/refresh")
async def refresh_tokens(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:

    # Extract refresh token from cookie
    refresh_token_str = request.cookies.get("refresh_token")

    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found"
        )

    # Validate refresh token
    payload = decode_token(refresh_token_str)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id = payload.get("sub")

    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    new_tokens = create_tokens(
        user_id=str(user.id),
        role=user.role.value,
        email=user.email,
        company_id=str(user.company_id) if user.company_id else None,
    )

    response.set_cookie(
        key="access_token",
        value=new_tokens["access_token"],
        max_age=900,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )

    logger.info(f"Token refreshed for user: {user.email}")

    return {
        "message": "Token refreshed successfully",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value,
        },
    }
