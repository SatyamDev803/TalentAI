import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import jwt
from passlib.context import CryptContext

from app.core.config import AuthConfig

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

settings = AuthConfig()


def hash_password(password: str) -> str:
    password = password[: settings.password_max_length]
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    role: str = "CANDIDATE",
    email: str = None,
    company_id: str = None,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str]:

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    if hasattr(role, "value"):  # Check if it's an enum
        role_str = role.value
    else:
        role_str = str(role)

    to_encode = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": jti,
        "type": "access",
        "role": role_str,
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

    if hasattr(role, "value"):
        role_value = role.value
    else:
        role_value = str(role)

    if company_id:
        company_id_str = str(company_id)
    else:
        company_id_str = None

    access_token, access_jti = create_access_token(
        user_id,
        role=role_value,
        email=email,
        company_id=company_id_str,
    )
    refresh_token, refresh_jti = create_refresh_token(user_id)

    return {
        "access_token": access_token,
        "access_jti": access_jti,
        "refresh_token": refresh_token,
        "refresh_jti": refresh_jti,
        "token_type": "bearer",
    }
