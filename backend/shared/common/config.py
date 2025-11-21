from pathlib import Path
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


def find_root_env() -> str:
    current = Path(__file__).resolve()

    # Traverse up until we find .env or reach filesystem root
    for parent in [current] + list(current.parents):
        env_file = parent / ".env"
        if env_file.exists():
            return str(env_file)

    # Fallback: assume standard project structure
    root = Path(__file__).resolve().parent.parent.parent.parent
    return str(root / ".env")


class BaseConfig(BaseSettings):
    model_config = ConfigDict(
        extra="ignore",
        env_file=find_root_env(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    # Environment
    environment: str = Field(default="local", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # PostgreSQL - Main Database
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="talentai_dev", alias="POSTGRES_USER")
    postgres_password: str = Field(
        default="dev_password_123", alias="POSTGRES_PASSWORD"
    )
    postgres_db: str = Field(default="talentai_db", alias="POSTGRES_DB")
    postgres_db_resume_parser: str = Field(
        default="talentai_resume", alias="POSTGRES_DB_RESUME_PARSER"
    )
    postgres_db_matching: str = Field(
        default="talentai_matching", alias="POSTGRES_DB_MATCHING"
    )

    # MongoDB
    mongodb_host: str = Field(default="localhost", alias="MONGODB_HOST")
    mongodb_port: int = Field(default=27017, alias="MONGODB_PORT")
    mongodb_user: str = Field(default="talentai_dev", alias="MONGODB_USER")
    mongodb_password: str = Field(default="dev_password_123", alias="MONGODB_PASSWORD")
    mongodb_db: str = Field(default="talentai_db", alias="MONGODB_DB")

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")
    redis_cache_ttl: int = Field(default=3600, alias="REDIS_CACHE_TTL")
    redis_max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")

    # Cache Settings
    enable_cache: bool = Field(default=True, alias="ENABLE_CACHE")
    cache_key_prefix: str = Field(default="talentai:resume:", alias="CACHE_KEY_PREFIX")

    # Service Ports
    auth_service_port: int = Field(default=8001, alias="AUTH_SERVICE_PORT")
    job_service_port: int = Field(default=8002, alias="JOB_SERVICE_PORT")
    resume_parser_service_port: int = Field(
        default=8003, alias="RESUME_PARSER_SERVICE_PORT"
    )
    matching_engine_service_port: int = Field(
        default=8004, alias="MATCHING_ENGINE_SERVICE_PORT"
    )
    ai_interview_service_port: int = Field(
        default=8005, alias="AI_INTERVIEW_SERVICE_PORT"
    )
    analytics_service_port: int = Field(default=8006, alias="ANALYTICS_SERVICE_PORT")
    workflow_service_port: int = Field(default=8007, alias="WORKFLOW_SERVICE_PORT")
    notification_service_port: int = Field(
        default=8008, alias="NOTIFICATION_SERVICE_PORT"
    )

    # JWT Configuration
    jwt_secret: str = Field(
        default="27412d937f74429dbfc99f56b58c41f23b4e357e8cda280b5f64515494aa194a",
        alias="JWT_SECRET",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ORIGINS"
    )

    # File Upload
    max_file_size: int = Field(default=10485760, alias="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: str = Field(default="pdf,docx,doc", alias="ALLOWED_EXTENSIONS")
    upload_dir: str = Field(default="./uploads/resumes", alias="UPLOAD_DIR")

    # ML Models
    spacy_model: str = Field(default="en_core_web_md", alias="SPACY_MODEL")
    sentence_transformer_model: str = Field(
        default="all-MiniLM-L6-v2", alias="SENTENCE_TRANSFORMER_MODEL"
    )
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")

    # Vector DB - ChromaDB only (pgvector removed for performance)
    chroma_persist_dir: str = Field(default="./chroma_data", alias="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(
        default="resumes", alias="CHROMA_COLLECTION_NAME"
    )

    # Celery
    celery_enabled: bool = Field(default=True, alias="CELERY_ENABLED")
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND"
    )

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=1000, alias="OPENAI_MAX_TOKENS")

    # Google Gemini
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    # LLM Provider Priority
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
    wandb_api_key: str = Field(default="", alias="WANDB_API_KEY")
    wandb_project: str = Field(default="talentai-resume-parser", alias="WANDB_PROJECT")
    wandb_entity: str = Field(default="", alias="WANDB_ENTITY")

    # Ray
    ray_enabled: bool = Field(default=True, alias="RAY_ENABLED")
    ray_dashboard_port: int = Field(default=8265, alias="RAY_DASHBOARD_PORT")
    ray_num_cpus: int = Field(default=4, alias="RAY_NUM_CPUS")

    weight_skill: float = Field(default=0.4, alias="WEIGHT_SKILL")
    weight_experience: float = Field(default=0.3, alias="WEIGHT_EXPERIENCE")
    weight_location: float = Field(default=0.15, alias="WEIGHT_LOCATION")
    weight_salary: float = Field(default=0.15, alias="WEIGHT_SALARY")
    max_llm_cost_per_day: float = Field(default=10.0, alias="MAX_LLM_COST_PER_DAY")

    # Tesseract
    tesseract_cmd: str = Field(
        default="/usr/local/bin/tesseract", alias="TESSERACT_CMD"
    )

    # BACKWARD COMPATIBILITY - Allow uppercase access
    @property
    def DEBUG(self) -> bool:
        """Backward compatibility for old services."""
        return self.debug

    @property
    def POSTGRES_HOST(self) -> str:
        return self.postgres_host

    @property
    def POSTGRES_PORT(self) -> int:
        return self.postgres_port

    @property
    def POSTGRES_USER(self) -> str:
        return self.postgres_user

    @property
    def POSTGRES_PASSWORD(self) -> str:
        return self.postgres_password

    @property
    def POSTGRES_DB(self) -> str:
        return self.postgres_db

    @property
    def MONGODB_HOST(self) -> str:
        return self.mongodb_host

    @property
    def MONGODB_PORT(self) -> int:
        return self.mongodb_port

    @property
    def MONGODB_USER(self) -> str:
        return self.mongodb_user

    @property
    def MONGODB_PASSWORD(self) -> str:
        return self.mongodb_password

    @property
    def MONGODB_DB(self) -> str:
        return self.mongodb_db

    @property
    def REDIS_HOST(self) -> str:
        return self.redis_host

    @property
    def REDIS_PORT(self) -> int:
        return self.redis_port

    @property
    def REDIS_DB(self) -> int:
        return self.redis_db

    @property
    def CORS_ORIGINS(self) -> str:
        return self.cors_origins

    # Computed Properties
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_resume(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db_resume_parser}"
        )

    @property
    def database_url_matching(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db_matching}"
        )

    @property
    def mongodb_url(self) -> str:
        return (
            f"mongodb://{self.mongodb_user}:{self.mongodb_password}"
            f"@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_db}"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment in ("development", "local")

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    @property
    def llm_provider_priority_list(self) -> list[str]:
        return [provider.strip() for provider in self.llm_provider_priority.split(",")]
