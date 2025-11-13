"""Add performance indexes for query optimization

Revision ID: b3f8d9e2c741
Revises: a6870f1c7d62
Create Date: 2025-11-12 14:20:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "b3f8d9e2c741"
down_revision: Union[str, Sequence[str], None] = "a6870f1c7d62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add performance indexes for common query patterns.

    FIRST: Convert JSON columns to JSONB (required for GIN indexes)
    THEN: Add performance indexes
    """

    print("🚀 Adding performance indexes...")

    # ═══════════════════════════════════════════════════════════
    # STEP 1: Convert JSON to JSONB (if needed)
    # ═══════════════════════════════════════════════════════════
    print("📦 Converting JSON columns to JSONB...")

    # Convert skills from JSON to JSONB
    op.execute("ALTER TABLE resumes ALTER COLUMN skills TYPE JSONB USING skills::jsonb")

    # Convert other JSON columns to JSONB for consistency
    op.execute(
        "ALTER TABLE resumes ALTER COLUMN experience TYPE JSONB USING experience::jsonb"
    )
    op.execute(
        "ALTER TABLE resumes ALTER COLUMN education TYPE JSONB USING education::jsonb"
    )
    op.execute(
        "ALTER TABLE resumes ALTER COLUMN certifications TYPE JSONB USING certifications::jsonb"
    )
    op.execute(
        "ALTER TABLE resumes ALTER COLUMN languages TYPE JSONB USING languages::jsonb"
    )

    print("✅ Converted JSON → JSONB")

    # ═══════════════════════════════════════════════════════════
    # STEP 2: Add Performance Indexes
    # ═══════════════════════════════════════════════════════════

    # 1. Composite index for user queries (most common pattern)
    op.create_index(
        "idx_resumes_user_not_deleted",
        "resumes",
        ["user_id", "is_deleted"],
        unique=False,
        postgresql_where=sa.text("is_deleted = false"),
    )
    print("✅ Created: idx_resumes_user_not_deleted")

    # 2. Index for ready-to-search resumes
    op.create_index(
        "idx_resumes_searchable",
        "resumes",
        ["user_id", "is_parsed", "is_embedding_generated"],
        unique=False,
        postgresql_where=sa.text(
            "is_deleted = false AND is_parsed = true AND is_embedding_generated = true"
        ),
    )
    print("✅ Created: idx_resumes_searchable")

    # 3. GIN index for JSONB skill search (NOW WORKS!)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_resumes_skills_gin 
        ON resumes USING gin(skills jsonb_path_ops)
    """
    )
    print("✅ Created: idx_resumes_skills_gin (GIN)")

    # 4. GIN index for experience search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_resumes_experience_gin 
        ON resumes USING gin(experience jsonb_path_ops)
    """
    )
    print("✅ Created: idx_resumes_experience_gin (GIN)")

    # 5. Index for date-based queries
    op.create_index(
        "idx_resumes_created_at_desc",
        "resumes",
        [sa.text("created_at DESC")],
        unique=False,
    )
    print("✅ Created: idx_resumes_created_at_desc")

    # 6. Index for last parsed timestamp
    op.create_index(
        "idx_resumes_last_parsed",
        "resumes",
        ["last_parsed_at"],
        unique=False,
        postgresql_where=sa.text("last_parsed_at IS NOT NULL"),
    )
    print("✅ Created: idx_resumes_last_parsed")

    # 7. Composite index for pagination
    op.create_index(
        "idx_resumes_user_created",
        "resumes",
        ["user_id", sa.text("created_at DESC")],
        unique=False,
    )
    print("✅ Created: idx_resumes_user_created")

    # 8. Full-text search index
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_resumes_fulltext 
        ON resumes 
        USING gin(
            to_tsvector('english', 
                COALESCE(full_name, '') || ' ' || 
                COALESCE(email, '') || ' ' || 
                COALESCE(summary, '') || ' ' ||
                COALESCE(ai_generated_summary, '')
            )
        )
    """
    )
    print("✅ Created: idx_resumes_fulltext")

    print("\n🎉 Migration complete!")
    print("   • Converted 5 columns: JSON → JSONB")
    print("   • Created 8 performance indexes")


def downgrade() -> None:
    """Remove performance indexes and revert JSONB to JSON."""

    print("🔄 Rolling back...")

    # Drop indexes
    op.drop_index("idx_resumes_fulltext", table_name="resumes")
    op.drop_index("idx_resumes_user_created", table_name="resumes")
    op.drop_index("idx_resumes_last_parsed", table_name="resumes")
    op.drop_index("idx_resumes_created_at_desc", table_name="resumes")
    op.drop_index("idx_resumes_experience_gin", table_name="resumes")
    op.drop_index("idx_resumes_skills_gin", table_name="resumes")
    op.drop_index("idx_resumes_searchable", table_name="resumes")
    op.drop_index("idx_resumes_user_not_deleted", table_name="resumes")

    # Revert JSONB to JSON (optional - JSONB is better, so you might want to keep it)
    # op.execute("ALTER TABLE resumes ALTER COLUMN skills TYPE JSON USING skills::json")
    # op.execute("ALTER TABLE resumes ALTER COLUMN experience TYPE JSON USING experience::json")
    # op.execute("ALTER TABLE resumes ALTER COLUMN education TYPE JSON USING education::json")
    # op.execute("ALTER TABLE resumes ALTER COLUMN certifications TYPE JSON USING certifications::json")
    # op.execute("ALTER TABLE resumes ALTER COLUMN languages TYPE JSON USING languages::json")

    print("✅ Rollback complete")
