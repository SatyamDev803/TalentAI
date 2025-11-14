from pathlib import Path
import sys
from pydantic import Field


shared_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "shared"
if str(shared_dir) not in sys.path:
    sys.path.insert(0, str(shared_dir))

from common.config import BaseConfig


class JobServiceConfig(BaseConfig):

    mongodb_host: str = Field(default="localhost", alias="MONGODB_HOST")
    mongodb_port: int = Field(default=27017, alias="MONGODB_PORT")
    mongodb_user: str = Field(default="root", alias="MONGODB_USER")
    mongodb_password: str = Field(default="root", alias="MONGODB_PASSWORD")
    mongodb_db: str = Field(default="talentai_jobs", alias="MONGODB_DB")

    @property
    def mongodb_url(self) -> str:
        return (
            f"mongodb://{self.mongodb_user}:{self.mongodb_password}@"
            f"{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_db}"
            "?authSource=admin"
        )

    @property
    def service_port(self) -> int:
        return self.job_service_port

    @property
    def service_name(self) -> str:
        return "Job Service"


settings = JobServiceConfig()
