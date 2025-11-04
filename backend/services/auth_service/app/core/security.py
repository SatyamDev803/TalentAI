"""Security utilities for authentication."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import jwt
from passlib.context import CryptContext

from app.core.config import AuthConfig

# Password hashing context - using argon2
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

settings = AuthConfig()


def hash_password(password: str) -> str:
    """Hash password using argon2."""
    password = password[: settings.password_max_length]
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    role: str = "CANDIDATE",
    email: str = None,
    company_id: str = None,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str]:
    """Create JWT access token with role, email, and company_id."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    to_encode = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": jti,
        "type": "access",
        "role": role,
        "email": email,
        "company_id": company_id,
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt, jti


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str]:
    """Create JWT refresh token."""
    if expires_delta is None:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)

    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    to_encode = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": jti,
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt, jti


def decode_token(token: str) -> Optional[Dict]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_tokens(
    user_id: str,
    role: str = "CANDIDATE",
    email: str = None,
    company_id: str = None,
) -> Dict[str, str]:
    """Create both access and refresh tokens."""
    access_token, access_jti = create_access_token(
        user_id,
        role=role,
        email=email,
        company_id=company_id,
    )
    refresh_token, refresh_jti = create_refresh_token(user_id)

    return {
        "access_token": access_token,
        "access_jti": access_jti,
        "refresh_token": refresh_token,
        "refresh_jti": refresh_jti,
        "token_type": "bearer",
    }
