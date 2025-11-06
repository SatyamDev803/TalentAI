from common.config import BaseConfig
from pydantic import ConfigDict, Field


class JobServiceConfig(BaseConfig):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    jwt_secret: str = Field(
        default="change-me-in-production-use-strong-secret",
        alias="JWT_SECRET",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        alias="JWT_ALGORITHM",
    )
    access_token_expire_minutes: int = Field(
        default=15,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )

    # Password Configuration
    password_min_length: int = 8
    password_max_length: int = 100

    # Redis Configuration for Token Blacklist
    redis_token_blacklist_prefix: str = "token_blacklist:"
    redis_refresh_token_prefix: str = "refresh_token:"
