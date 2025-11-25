from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    Enum as SQLEnum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta, timezone
import uuid
import enum

from app.db.base import Base


class QualityTier(str, enum.Enum):
    # Quality tier classification for candidate matches

    # TIER_1: 85-100 (Excellent match)
    # TIER_2: 70-84 (Strong match)
    # TIER_3: 55-69 (Moderate match)
    # TIER_4: 40-54 (Weak match)
    # TIER_5: 0-39 (Poor match)

    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"
    TIER_4 = "TIER_4"
    TIER_5 = "TIER_5"


class Recommendation(str, enum.Enum):
    STRONG_HIRE = "STRONG_HIRE"  # 85+ score
    HIRE = "HIRE"  # 70-84 score
    CONSIDER = "CONSIDER"  # 55-69 score
    PASS = "PASS"  # <55 score


class MatchScore(Base):

    __tablename__ = "match_scores"

    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Scoring breakdown
    overall_score = Column(Float, nullable=False)
    skill_score = Column(Float)
    experience_score = Column(Float)
    location_score = Column(Float)
    salary_score = Column(Float)

    # ML predictions
    ml_quality_tier = Column(SQLEnum(QualityTier))
    ml_confidence = Column(Float)

    # LLM-generated insights
    explanation = Column(Text)
    strengths = Column(Text)
    gaps = Column(Text)
    recommendation = Column(SQLEnum(Recommendation))

    # Processing metadata
    ray_task_id = Column(String(255))
    chroma_used = Column(Boolean, default=False)
    processing_time_ms = Column(Integer)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1),
        nullable=False,
    )

    # Indexes and constraints
    __table_args__ = (
        # Composite indexes for common queries
        Index("idx_job_score", "job_id", "overall_score"),
        Index("idx_candidate_score", "candidate_id", "overall_score"),
        Index("idx_quality_tier", "ml_quality_tier"),
        Index("idx_recommendation", "recommendation"),
        Index("idx_expires_at", "expires_at"),
        Index("idx_created_at", "created_at"),
        # Unique constraint to prevent duplicate matches
        UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job_match"),
    )

    def __repr__(self):
        return (
            f"<MatchScore(id={self.id}, "
            f"job={self.job_id}, "
            f"candidate={self.candidate_id}, "
            f"score={self.overall_score}, "
            f"tier={self.ml_quality_tier})>"
        )

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def age_hours(self) -> float:
        delta = datetime.now(timezone.utc) - self.created_at
        return delta.total_seconds() / 3600

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "candidate_id": str(self.candidate_id),
            "job_id": str(self.job_id),
            "overall_score": self.overall_score,
            "breakdown": {
                "skill": self.skill_score,
                "experience": self.experience_score,
                "location": self.location_score,
                "salary": self.salary_score,
            },
            "ml_quality_tier": (
                self.ml_quality_tier.value if self.ml_quality_tier else None
            ),
            "ml_confidence": self.ml_confidence,
            "explanation": self.explanation,
            "strengths": self.strengths,
            "gaps": self.gaps,
            "recommendation": (
                self.recommendation.value if self.recommendation else None
            ),
            "ray_task_id": self.ray_task_id,
            "chroma_used": self.chroma_used,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired,
            "age_hours": round(self.age_hours, 2),
        }


class MLModel(Base):

    __tablename__ = "ml_models"

    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(50), nullable=False)
    model_type = Column(String(100))  # "xgboost", "random_forest", "neural_net"

    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)

    # Lifecycle timestamps
    training_date = Column(DateTime(timezone=True))
    deployment_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    retired_at = Column(DateTime(timezone=True))

    # External tracking IDs
    mlflow_run_id = Column(String(255))
    ray_model_id = Column(String(255))

    # Status
    is_active = Column(Boolean, default=True, index=True, nullable=False)

    # Indexes and constraints
    __table_args__ = (
        Index("idx_model_active", "is_active", "deployment_date"),
        Index("idx_model_name_version", "model_name", "model_version"),
        UniqueConstraint("model_name", "model_version", name="uq_model_name_version"),
    )

    def __repr__(self):
        return (
            f"<MLModel(id={self.id}, "
            f"name={self.model_name}, "
            f"version={self.model_version}, "
            f"type={self.model_type}, "
            f"active={self.is_active})>"
        )

    @property
    def age_days(self) -> float:
        if self.deployment_date:
            delta = datetime.now(timezone.utc) - self.deployment_date
            return delta.total_seconds() / 86400
        return 0.0

    @property
    def is_retired(self) -> bool:
        return self.retired_at is not None

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "model_name": self.model_name,
            "model_version": self.model_version,
            "model_type": self.model_type,
            "metrics": {
                "accuracy": self.accuracy,
                "precision": self.precision,
                "recall": self.recall,
                "f1_score": self.f1_score,
            },
            "training_date": (
                self.training_date.isoformat() if self.training_date else None
            ),
            "deployment_date": (
                self.deployment_date.isoformat() if self.deployment_date else None
            ),
            "retired_at": self.retired_at.isoformat() if self.retired_at else None,
            "mlflow_run_id": self.mlflow_run_id,
            "ray_model_id": self.ray_model_id,
            "is_active": self.is_active,
            "is_retired": self.is_retired,
            "age_days": round(self.age_days, 2),
        }
