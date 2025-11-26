"""Add file_hash and ai_generated_summary fields

Revision ID: a6870f1c7d62
Revises:
Create Date: 2025-11-10 16:17:43.890506
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "a6870f1c7d62"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add file_hash column
    op.add_column(
        "resumes", sa.Column("file_hash", sa.String(length=64), nullable=True)
    )
    op.create_index(
        op.f("ix_resumes_file_hash"), "resumes", ["file_hash"], unique=False
    )

    # Add ai_generated_summary column
    op.add_column(
        "resumes", sa.Column("ai_generated_summary", sa.Text(), nullable=True)
    )

    # HNSW index
    op.execute(
        "CREATE INDEX IF NOT EXISTS resumes_embedding_hnsw_idx ON resumes "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop HNSW index
    op.execute("DROP INDEX IF EXISTS resumes_embedding_hnsw_idx")

    # Remove columns
    op.drop_index(op.f("ix_resumes_file_hash"), table_name="resumes")
    op.drop_column("resumes", "ai_generated_summary")
    op.drop_column("resumes", "file_hash")
