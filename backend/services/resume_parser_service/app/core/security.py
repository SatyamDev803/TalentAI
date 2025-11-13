"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT access token with detailed debugging."""
    try:
        # Step 1: Decode without verification to see contents
        unverified = jwt.decode(token, options={"verify_signature": False})
        print(f"\n🔍 === TOKEN DEBUG ===")
        print(f"Token (first 50 chars): {token[:50]}...")
        print(f"Unverified payload: {unverified}")
        print(f"Token exp: {unverified.get('exp')}")
        print(f"Token iat: {unverified.get('iat')}")
        print(f"Current timestamp: {int(datetime.now(timezone.utc).timestamp())}")
        print(f"JWT Secret (first 20 chars): {settings.jwt_secret[:20]}...")
        print(f"JWT Algorithm: {settings.jwt_algorithm}")

        # Check if token is expired
        exp = unverified.get("exp")
        now = int(datetime.now(timezone.utc).timestamp())
        if exp and exp < now:
            print(f"❌ Token is EXPIRED! Exp: {exp}, Now: {now}, Diff: {exp - now}s")
        else:
            print(f"✅ Token is NOT expired. Time until expiry: {exp - now}s")

        # Step 2: Now verify with signature
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        print(f"✅ TOKEN VERIFIED SUCCESSFULLY!")
        print(f"===================\n")
        return payload

    except ExpiredSignatureError as e:
        print(f"❌ Token EXPIRED: {e}")
        print(f"===================\n")
        return None
    except InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
        print(f"===================\n")
        return None
    except PyJWTError as e:
        print(f"❌ JWT error: {e}")
        print(f"===================\n")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        print(f"===================\n")
        return None


def validate_token(token: str) -> bool:
    """Validate JWT token."""
    payload = decode_access_token(token)
    return payload is not None
