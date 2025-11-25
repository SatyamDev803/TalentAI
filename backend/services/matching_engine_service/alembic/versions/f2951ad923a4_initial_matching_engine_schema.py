"""initial_matching_engine_schema

Revision ID: f2951ad923a4
Revises:
Create Date: 2025-11-17

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

revision: str = "f2951ad923a4"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for matching engine"""

    # Create ENUM types - wrap in try/except to handle if they already exist
    try:
        op.execute(
            "CREATE TYPE qualitytier AS ENUM ('TIER_1', 'TIER_2', 'TIER_3', 'TIER_4', 'TIER_5')"
        )
    except Exception:
        pass

    try:
        op.execute(
            "CREATE TYPE recommendation AS ENUM ('STRONG_HIRE', 'HIRE', 'CONSIDER', 'PASS')"
        )
    except Exception:
        pass

    try:
        op.execute(
            "CREATE TYPE syncstatus AS ENUM ('pending', 'in_progress', 'success', 'partial', 'failed')"
        )
    except Exception:
        pass

    # Define ENUM objects for use in columns
    quality_tier = postgresql.ENUM(
        "TIER_1",
        "TIER_2",
        "TIER_3",
        "TIER_4",
        "TIER_5",
        name="qualitytier",
        create_type=False,
    )
    recommendation_enum = postgresql.ENUM(
        "STRONG_HIRE",
        "HIRE",
        "CONSIDER",
        "PASS",
        name="recommendation",
        create_type=False,
    )
    sync_status = postgresql.ENUM(
        "pending",
        "in_progress",
        "success",
        "partial",
        "failed",
        name="syncstatus",
        create_type=False,
    )

    # Table 1: match_scores
    op.create_table(
        "match_scores",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("skill_score", sa.Float(), nullable=True),
        sa.Column("experience_score", sa.Float(), nullable=True),
        sa.Column("location_score", sa.Float(), nullable=True),
        sa.Column("salary_score", sa.Float(), nullable=True),
        sa.Column("ml_quality_tier", quality_tier, nullable=True),
        sa.Column("ml_confidence", sa.Float(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("gaps", sa.Text(), nullable=True),
        sa.Column("recommendation", recommendation_enum, nullable=True),
        sa.Column("ray_task_id", sa.String(255), nullable=True),
        sa.Column("chroma_used", sa.Boolean(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )

    # Indexes for match_scores
    op.create_index("idx_candidate_id", "match_scores", ["candidate_id"])
    op.create_index("idx_job_id", "match_scores", ["job_id"])
    op.create_index("idx_created_at", "match_scores", ["created_at"])
    op.create_index("idx_expires_at", "match_scores", ["expires_at"])
    op.create_index(
        "idx_candidate_score", "match_scores", ["candidate_id", "overall_score"]
    )
    op.create_index("idx_job_score", "match_scores", ["job_id", "overall_score"])

    # Table 2: ml_models
    op.create_table(
        "ml_models",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("model_type", sa.String(100), nullable=True),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("precision", sa.Float(), nullable=True),
        sa.Column("recall", sa.Float(), nullable=True),
        sa.Column("f1_score", sa.Float(), nullable=True),
        sa.Column("training_date", sa.DateTime(), nullable=True),
        sa.Column("deployment_date", sa.DateTime(), nullable=True),
        sa.Column("retired_at", sa.DateTime(), nullable=True),
        sa.Column("mlflow_run_id", sa.String(255), nullable=True),
        sa.Column("ray_model_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
    )

    op.create_index("idx_ml_models_is_active", "ml_models", ["is_active"])

    # Table 3: vector_sync_audit
    op.create_table(
        "vector_sync_audit",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sync_status, nullable=False, server_default="pending"),
        sa.Column("chroma_synced", sa.Boolean(), server_default="false"),
        sa.Column("consistency_check", sa.Boolean(), server_default="false"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    # Indexes for vector_sync_audit
    op.create_index("ix_vector_sync_entity_id", "vector_sync_audit", ["entity_id"])
    op.create_index("ix_vector_sync_entity_type", "vector_sync_audit", ["entity_type"])
    op.create_index("ix_vector_sync_status", "vector_sync_audit", ["status"])


def downgrade() -> None:
    op.drop_table("vector_sync_audit")
    op.drop_table("ml_models")
    op.drop_table("match_scores")

    # Drop ENUM types
    postgresql.ENUM(name="syncstatus").drop(op.get_bind())
    postgresql.ENUM(name="recommendation").drop(op.get_bind())
    postgresql.ENUM(name="qualitytier").drop(op.get_bind())
