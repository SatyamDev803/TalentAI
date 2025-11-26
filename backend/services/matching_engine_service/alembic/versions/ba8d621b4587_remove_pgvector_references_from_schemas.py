"""Remove pgvector references from schemas

Revision ID: ba8d621b4587
Revises: f2951ad923a4
Create Date: 2025-11-20 11:05:58.358649

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "ba8d621b4587"
down_revision: Union[str, Sequence[str], None] = "f2951ad923a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_vector_sync_entity_id"), table_name="vector_sync_audit")
    op.drop_index(op.f("ix_vector_sync_entity_type"), table_name="vector_sync_audit")
    op.drop_index(op.f("ix_vector_sync_status"), table_name="vector_sync_audit")
    op.drop_table("vector_sync_audit")
    op.drop_index(op.f("idx_candidate_id"), table_name="match_scores")
    op.drop_index(op.f("idx_created_at"), table_name="match_scores")
    op.drop_index(op.f("idx_job_id"), table_name="match_scores")
    op.create_index(
        op.f("ix_match_scores_candidate_id"),
        "match_scores",
        ["candidate_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_match_scores_job_id"), "match_scores", ["job_id"], unique=False
    )
    op.drop_column("match_scores", "pgvector_used")
    op.drop_index(op.f("idx_ml_models_is_active"), table_name="ml_models")
    op.create_index(
        op.f("ix_ml_models_is_active"), "ml_models", ["is_active"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ml_models_is_active"), table_name="ml_models")
    op.create_index(
        op.f("idx_ml_models_is_active"), "ml_models", ["is_active"], unique=False
    )
    op.add_column(
        "match_scores",
        sa.Column("pgvector_used", sa.BOOLEAN(), autoincrement=False, nullable=True),
    )
    op.drop_index(op.f("ix_match_scores_job_id"), table_name="match_scores")
    op.drop_index(op.f("ix_match_scores_candidate_id"), table_name="match_scores")
    op.create_index(op.f("idx_job_id"), "match_scores", ["job_id"], unique=False)
    op.create_index(
        op.f("idx_created_at"), "match_scores", ["created_at"], unique=False
    )
    op.create_index(
        op.f("idx_candidate_id"), "match_scores", ["candidate_id"], unique=False
    )
    op.create_table(
        "vector_sync_audit",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "entity_type", sa.VARCHAR(length=50), autoincrement=False, nullable=False
        ),
        sa.Column("entity_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "in_progress",
                "success",
                "partial",
                "failed",
                name="syncstatus",
            ),
            server_default=sa.text("'pending'::syncstatus"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "chroma_synced",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "pgvector_synced",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "consistency_check",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("error_message", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "started_at",
            postgresql.TIMESTAMP(),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "completed_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("vector_sync_audit_pkey")),
    )
    op.create_index(
        op.f("ix_vector_sync_status"), "vector_sync_audit", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_vector_sync_entity_type"),
        "vector_sync_audit",
        ["entity_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_vector_sync_entity_id"),
        "vector_sync_audit",
        ["entity_id"],
        unique=False,
    )
