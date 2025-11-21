"""Change embedding column from pgvector to JSON

Revision ID: 3f2ad4657e60
Revises: b3f8d9e2c741
Create Date: 2025-11-20 11:11:30.566900

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3f2ad4657e60"
down_revision: Union[str, Sequence[str], None] = "b3f8d9e2c741"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - drop unused indexes and remove pgvector support."""
    # Drop indexes that are no longer needed
    op.drop_index(op.f("idx_resumes_created_at_desc"), table_name="resumes")
    op.drop_index(
        op.f("idx_resumes_experience_gin"),
        table_name="resumes",
        postgresql_ops={"experience": "jsonb_path_ops"},
        postgresql_using="gin",
    )
    op.drop_index(
        op.f("idx_resumes_fulltext"), table_name="resumes", postgresql_using="gin"
    )
    op.drop_index(
        op.f("idx_resumes_last_parsed"),
        table_name="resumes",
        postgresql_where="(last_parsed_at IS NOT NULL)",
    )
    op.drop_index(
        op.f("idx_resumes_searchable"),
        table_name="resumes",
        postgresql_where="((is_deleted = false) AND (is_parsed = true) AND (is_embedding_generated = true))",
    )
    op.drop_index(
        op.f("idx_resumes_skills_gin"),
        table_name="resumes",
        postgresql_ops={"skills": "jsonb_path_ops"},
        postgresql_using="gin",
    )
    op.drop_index(op.f("idx_resumes_user_created"), table_name="resumes")
    op.drop_index(
        op.f("idx_resumes_user_not_deleted"),
        table_name="resumes",
        postgresql_where="(is_deleted = false)",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate dropped indexes
    op.create_index(
        op.f("idx_resumes_user_not_deleted"),
        "resumes",
        ["user_id", "is_deleted"],
        unique=False,
        postgresql_where="(is_deleted = false)",
    )
    op.create_index(
        op.f("idx_resumes_user_created"),
        "resumes",
        ["user_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_index(
        op.f("idx_resumes_skills_gin"),
        "resumes",
        ["skills"],
        unique=False,
        postgresql_ops={"skills": "jsonb_path_ops"},
        postgresql_using="gin",
    )
    op.create_index(
        op.f("idx_resumes_searchable"),
        "resumes",
        ["user_id", "is_parsed", "is_embedding_generated"],
        unique=False,
        postgresql_where="((is_deleted = false) AND (is_parsed = true) AND (is_embedding_generated = true))",
    )
    op.create_index(
        op.f("idx_resumes_last_parsed"),
        "resumes",
        ["last_parsed_at"],
        unique=False,
        postgresql_where="(last_parsed_at IS NOT NULL)",
    )
    op.create_index(
        op.f("idx_resumes_fulltext"),
        "resumes",
        [
            sa.literal_column(
                "to_tsvector('english'::regconfig, (((((COALESCE(full_name, ''::character varying)::text || ' '::text) || COALESCE(email, ''::character varying)::text) || ' '::text) || COALESCE(summary, ''::text)) || ' '::text) || COALESCE(ai_generated_summary, ''::text))"
            )
        ],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        op.f("idx_resumes_experience_gin"),
        "resumes",
        ["experience"],
        unique=False,
        postgresql_ops={"experience": "jsonb_path_ops"},
        postgresql_using="gin",
    )
    op.create_index(
        op.f("idx_resumes_created_at_desc"),
        "resumes",
        [sa.literal_column("created_at DESC")],
        unique=False,
    )
