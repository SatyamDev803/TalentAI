from common.config import BaseConfig
from pydantic import Field


class AuthConfig(BaseConfig):
    """Auth Service configuration extending BaseConfig.

    Inherits all shared configuration from BaseConfig including:
    - JWT settings (jwt_secret, jwt_algorithm, access_token_expire_minutes, etc.)
    - Database connections (PostgreSQL, MongoDB, Redis)
    - Service ports
    - And more...
    """

    # Password Configuration (Auth-specific)
    password_min_length: int = Field(default=8, alias="PASSWORD_MIN_LENGTH")
    password_max_length: int = Field(default=100, alias="PASSWORD_MAX_LENGTH")

    # Redis Configuration for Token Blacklist (Auth-specific)
    redis_token_blacklist_prefix: str = Field(
        default="token_blacklist:", alias="REDIS_TOKEN_BLACKLIST_PREFIX"
    )
    redis_refresh_token_prefix: str = Field(
        default="refresh_token:", alias="REDIS_REFRESH_TOKEN_PREFIX"
    )

    # Override service_name property
    @property
    def service_name(self) -> str:
        """Get service name."""
        return "Auth Service"

    @property
    def service_port(self) -> int:
        """Get auth service port."""
        return self.auth_service_port
