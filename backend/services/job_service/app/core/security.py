from typing import Dict, Optional

import jwt
from common.logging import get_logger

from app.core.config import settings

logger = get_logger(__name__)


def decode_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid token: {e}")
        return None
