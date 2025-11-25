import sys
from pathlib import Path

from pydantic import Field

shared_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "shared"
if str(shared_dir) not in sys.path:
    sys.path.insert(0, str(shared_dir))

from common.config import BaseConfig


class Settings(BaseConfig):
    chroma_persist_dir: str = Field(default="./chroma_data", env="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(default="resumes", env="CHROMA_COLLECTION_NAME")

    sentence_transformer_model: str = Field(
        default="all-MiniLM-L6-v2", env="SENTENCE_TRANSFORMER_MODEL"
    )
    embedding_dimension: int = Field(default=384, env="EMBEDDING_DIMENSION")

    @property
    def SERVICE_NAME(self) -> str:
        return "matching-engine-service"

    @property
    def PORT(self) -> int:
        return self.matching_engine_service_port

    @property
    def DATABASE_URL_MATCHING(self) -> str:
        return self.database_url_matching

    @property
    def matching_weights(self) -> dict:
        return {
            "skill": self.weight_skill,
            "experience": self.weight_experience,
            "location": self.weight_location,
            "salary": self.weight_salary,
        }

    @property
    def llm_config(self) -> dict:
        return {
            "google_api_key": self.google_api_key,
            "gemini_model": self.gemini_model,
            "openai_api_key": self.openai_api_key,
            "openai_model": self.openai_model,
            "provider_priority": self.llm_provider_priority_list,
        }

    @property
    def ray_config(self) -> dict:
        return {
            "enabled": self.ray_enabled,
            "num_cpus": self.ray_num_cpus,
            "dashboard_port": self.ray_dashboard_port,
        }


settings = Settings()
