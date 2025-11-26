from typing import Optional

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError

from app.core.config import settings
from common.logging import get_logger

logger = get_logger(__name__)


def decode_access_token(token: str) -> Optional[dict]:

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload

    except ExpiredSignatureError:
        logger.info("Token expired for user (normal expiration)")
        return None
    except InvalidTokenError as e:
        logger.info(f"Invalid token structure: {str(e)[:50]}")
        return None

    except PyJWTError as e:
        logger.warning(f"JWT error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected token decode error: {type(e).__name__}: {e}")
        return None


def validate_token(token: str) -> bool:

    payload = decode_access_token(token)
    return payload is not None


def extract_user_id(token: str) -> Optional[str]:

    payload = decode_access_token(token)
    if payload:
        return payload.get("sub")
    return None


def extract_user_role(token: str) -> Optional[str]:

    payload = decode_access_token(token)
    if payload:
        return payload.get("role")
    return None


def extract_company_id(token: str) -> Optional[str]:

    payload = decode_access_token(token)
    if payload:
        return payload.get("company_id")
    return None
