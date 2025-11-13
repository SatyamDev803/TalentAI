"""create_resume_table_with_pgvector

Revision ID: ac6eb147ec44
Revises: 2fac6ab29008
Create Date: 2025-11-10 13:35:21.785267
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "ac6eb147ec44"
down_revision: Union[str, Sequence[str], None] = "2fac6ab29008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop old table if exists
    op.drop_index(
        op.f("ix_resume_skills_resume_id"), table_name="resume_skills", if_exists=True
    )
    op.drop_table("resume_skills", if_exists=True)

    # Add new columns to resumes table
    op.add_column("resumes", sa.Column("parsed_text", sa.Text(), nullable=True))
    op.add_column(
        "resumes", sa.Column("total_experience_years", sa.Float(), nullable=True)
    )
    op.add_column(
        "resumes", sa.Column("embedding_model", sa.String(length=100), nullable=True)
    )
    op.add_column("resumes", sa.Column("skills", sa.JSON(), nullable=True))
    op.add_column("resumes", sa.Column("experience", sa.JSON(), nullable=True))
    op.add_column("resumes", sa.Column("education", sa.JSON(), nullable=True))
    op.add_column("resumes", sa.Column("certifications", sa.JSON(), nullable=True))
    op.add_column("resumes", sa.Column("languages", sa.JSON(), nullable=True))
    op.add_column(
        "resumes",
        sa.Column("is_parsed", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "resumes",
        sa.Column(
            "is_embedding_generated",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.add_column("resumes", sa.Column("parsing_error", sa.Text(), nullable=True))
    op.add_column(
        "resumes", sa.Column("parsing_version", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "resumes",
        sa.Column("last_parsed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "resumes",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Alter existing column
    op.alter_column(
        "resumes",
        "phone",
        existing_type=sa.VARCHAR(length=20),
        type_=sa.String(length=50),
        existing_nullable=True,
    )

    # Drop old index
    op.execute("DROP INDEX IF EXISTS resumes_embedding_idx")

    # Create new indexes
    op.create_index(op.f("ix_resumes_email"), "resumes", ["email"], unique=False)
    op.create_index(op.f("ix_resumes_id"), "resumes", ["id"], unique=False)

    # Create HNSW vector index (better than IVFFlat for similarity search)
    op.execute(
        "CREATE INDEX resumes_embedding_hnsw_idx ON resumes "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # Drop old columns
    op.drop_column("resumes", "quality_score", if_exists=True)
    op.drop_column("resumes", "parsed_at", if_exists=True)
    op.drop_column("resumes", "parsing_status", if_exists=True)
    op.drop_column("resumes", "embedding_generated", if_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Add back old columns
    op.add_column(
        "resumes",
        sa.Column(
            "embedding_generated",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "resumes",
        sa.Column(
            "parsing_status",
            sa.VARCHAR(length=50),
            server_default=sa.text("'pending'::character varying"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "resumes",
        sa.Column(
            "parsed_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "resumes",
        sa.Column(
            "quality_score",
            sa.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
    )

    # Drop new indexes
    op.drop_index(op.f("ix_resumes_id"), table_name="resumes")
    op.drop_index(op.f("ix_resumes_email"), table_name="resumes")
    op.execute("DROP INDEX IF EXISTS resumes_embedding_hnsw_idx")

    # Recreate old index
    op.execute(
        "CREATE INDEX resumes_embedding_idx ON resumes "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # Alter column back
    op.alter_column(
        "resumes",
        "phone",
        existing_type=sa.String(length=50),
        type_=sa.VARCHAR(length=20),
        existing_nullable=True,
    )

    # Drop new columns
    op.drop_column("resumes", "is_deleted")
    op.drop_column("resumes", "last_parsed_at")
    op.drop_column("resumes", "parsing_version")
    op.drop_column("resumes", "parsing_error")
    op.drop_column("resumes", "is_embedding_generated")
    op.drop_column("resumes", "is_parsed")
    op.drop_column("resumes", "languages")
    op.drop_column("resumes", "certifications")
    op.drop_column("resumes", "education")
    op.drop_column("resumes", "experience")
    op.drop_column("resumes", "skills")
    op.drop_column("resumes", "embedding_model")
    op.drop_column("resumes", "total_experience_years")
    op.drop_column("resumes", "parsed_text")

    # Recreate resume_skills table
    op.create_table(
        "resume_skills",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("resume_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("skill_id", sa.UUID(), autoincrement=False, nullable=True),
        sa.Column(
            "skill_name", sa.VARCHAR(length=255), autoincrement=False, nullable=False
        ),
        sa.Column(
            "skill_category", sa.VARCHAR(length=100), autoincrement=False, nullable=True
        ),
        sa.Column(
            "proficiency_level",
            sa.VARCHAR(length=50),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "years_of_experience", sa.INTEGER(), autoincrement=False, nullable=True
        ),
        sa.Column(
            "embedding_generated", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
        sa.Column(
            "confidence_score",
            sa.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "extraction_method",
            sa.VARCHAR(length=50),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "mentioned_in_section",
            sa.VARCHAR(length=100),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "extracted_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["resume_id"], ["resumes.id"], name="resume_skills_resume_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="resume_skills_pkey"),
    )
    op.create_index(
        "ix_resume_skills_resume_id", "resume_skills", ["resume_id"], unique=False
    )
