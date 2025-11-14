"""add_vector_embedding_to_resumes

Revision ID: 2fac6ab29008
Revises:
Create Date: 2025-11-09 16:56:36.852355

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "2fac6ab29008"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema:
    1. Enable pgvector extension
    2. Add embedding column
    3. Make embedding_generated NOT NULL with default
    4. Make parsing_status NOT NULL
    5. Create vector index for fast similarity search
    """

    # 1. Enable pgvector extension (safe to run multiple times)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    print("pgvector extension enabled")

    # 2. Add embedding column (384 dimensions for all-MiniLM-L6-v2)
    op.add_column("resumes", sa.Column("embedding", Vector(384), nullable=True))
    print("Added embedding column (384D)")

    # 3. Make embedding_generated NOT NULL with default
    op.alter_column(
        "resumes",
        "embedding_generated",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default="false",
    )
    print("Set embedding_generated to NOT NULL with default")

    # 4. Make parsing_status NOT NULL
    op.alter_column(
        "resumes",
        "parsing_status",
        existing_type=sa.VARCHAR(length=50),
        nullable=False,
        server_default="pending",
    )
    print("Set parsing_status to NOT NULL with default")

    # 5. Create vector index for cosine similarity search
    # Using ivfflat index - best for ~1M vectors or less
    # lists = sqrt(n_rows) is a good starting point (we use 100)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS resumes_embedding_idx 
        ON resumes 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """
    )
    print("Created vector similarity search index")

    print("Migration complete!")


def downgrade() -> None:
    """
    Downgrade schema:
    Remove vector embedding support
    """

    # 1. Drop vector index
    op.execute("DROP INDEX IF EXISTS resumes_embedding_idx")
    print("Dropped vector index")

    # 2. Revert parsing_status nullable
    op.alter_column(
        "resumes", "parsing_status", existing_type=sa.VARCHAR(length=50), nullable=True
    )

    # 3. Revert embedding_generated nullable
    op.alter_column(
        "resumes", "embedding_generated", existing_type=sa.Boolean(), nullable=True
    )

    # 4. Drop embedding column
    op.drop_column("resumes", "embedding")
    print("Removed embedding column")

    # Note: We don't drop the vector extension as other tables might use it

    print("Downgrade complete")
