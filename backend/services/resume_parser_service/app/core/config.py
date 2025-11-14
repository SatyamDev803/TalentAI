from functools import lru_cache
import sys
from pathlib import Path
from typing import Optional

from pydantic import Field

shared_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "shared"
if str(shared_dir) not in sys.path:
    sys.path.insert(0, str(shared_dir))

from common.config import BaseConfig


class ResumeParserConfig(BaseConfig):
    # File Upload
    max_file_size: int = Field(default=10485760, alias="MAX_FILE_SIZE")
    allowed_extensions: str = Field(default="pdf,docx,doc", alias="ALLOWED_EXTENSIONS")
    upload_dir: str = Field(default="./uploads/resumes", alias="UPLOAD_DIR")

    # ML Models
    spacy_model: str = Field(default="en_core_web_md", alias="SPACY_MODEL")
    sentence_transformer_model: str = Field(
        default="all-MiniLM-L6-v2", alias="SENTENCE_TRANSFORMER_MODEL"
    )
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")

    # Vector DBs
    pgvector_enabled: bool = Field(default=True, alias="PGVECTOR_ENABLED")
    chroma_persist_dir: str = Field(default="./chroma_data", alias="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(
        default="resumes", alias="CHROMA_COLLECTION_NAME"
    )

    # Redis Configuration
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_cache_ttl: int = Field(default=3600, alias="REDIS_CACHE_TTL")
    redis_max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")

    # Cache Settings
    enable_cache: bool = Field(default=True, alias="ENABLE_CACHE")
    cache_key_prefix: str = Field(default="talentai:resume:", alias="CACHE_KEY_PREFIX")

    # CELERY Configuration
    CELERY_ENABLED: bool = Field(default=False, alias="CELERY_ENABLED")
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0", alias="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND"
    )

    # AI/LLM Configuration
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=1000, alias="OPENAI_MAX_TOKENS")

    llm_provider_priority: str = Field(
        default="gemini,openai,fallback", alias="LLM_PROVIDER_PRIORITY"
    )

    # MLflow
    mlflow_tracking_uri: str = Field(
        default="http://localhost:5000", alias="MLFLOW_TRACKING_URI"
    )
    mlflow_experiment_name: str = Field(
        default="resume-parser", alias="MLFLOW_EXPERIMENT_NAME"
    )

    # Weights & Biases
    wandb_api_key: Optional[str] = Field(default=None, alias="WANDB_API_KEY")
    wandb_project: str = Field(default="talentai-resume-parser", alias="WANDB_PROJECT")
    wandb_entity: Optional[str] = Field(default=None, alias="WANDB_ENTITY")

    # Ray
    ray_enabled: bool = Field(default=True, alias="RAY_ENABLED")
    ray_dashboard_port: int = Field(default=8265, alias="RAY_DASHBOARD_PORT")
    ray_num_cpus: int = Field(default=4, alias="RAY_NUM_CPUS")

    # Tesseract
    tesseract_cmd: str = Field(
        default="/usr/local/bin/tesseract", alias="TESSERACT_CMD"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    @property
    def llm_providers_list(self) -> list[str]:
        return [p.strip() for p in self.llm_provider_priority.split(",")]

    @property
    def service_port(self) -> int:
        return self.resume_parser_service_port

    @property
    def database_url(self) -> str:
        return self.database_url_resume

    @property
    def service_name(self) -> str:
        return "Resume Parser Service"

    @property
    def embedding_model_name(self) -> str:
        return self.sentence_transformer_model

    @property
    def vector_dimension(self) -> int:
        return self.embedding_dimension


@lru_cache
def get_settings() -> ResumeParserConfig:
    return ResumeParserConfig()


settings = get_settings()
