from pathlib import Path
import sys
from pydantic import Field

shared_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "shared"
if str(shared_dir) not in sys.path:
    sys.path.insert(0, str(shared_dir))

from common.config import BaseConfig


class AuthConfig(BaseConfig):

    # Password Configuration
    password_min_length: int = Field(default=8, alias="PASSWORD_MIN_LENGTH")
    password_max_length: int = Field(default=100, alias="PASSWORD_MAX_LENGTH")

    # Redis Configuration for Token Blacklist
    redis_token_blacklist_prefix: str = Field(
        default="token_blacklist:", alias="REDIS_TOKEN_BLACKLIST_PREFIX"
    )
    redis_refresh_token_prefix: str = Field(
        default="refresh_token:", alias="REDIS_REFRESH_TOKEN_PREFIX"
    )

    @property
    def service_name(self) -> str:
        return "Auth Service"

    @property
    def service_port(self) -> int:
        return self.auth_service_port


settings = AuthConfig()
