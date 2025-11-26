"""Fix timezone awareness and add constraints

Revision ID: dd392f3a61db
Revises: ba8d621b4587
Create Date: 2025-11-25 14:21:36.958859

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "dd392f3a61db"
down_revision: Union[str, Sequence[str], None] = "ba8d621b4587"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    print("Cleaning duplicate match_scores...")

    op.execute(
        """
        DELETE FROM match_scores
        WHERE id NOT IN (
            SELECT DISTINCT ON (candidate_id, job_id) id
            FROM match_scores
            ORDER BY candidate_id, job_id, overall_score DESC, created_at DESC
        );
    """
    )

    print("Duplicate cleanup complete")

    print("Fixing NULL timestamps...")

    op.execute(
        """
        UPDATE match_scores 
        SET created_at = CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
        WHERE created_at IS NULL
    """
    )

    op.execute(
        """
        UPDATE match_scores 
        SET expires_at = (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') + INTERVAL '1 day'
        WHERE expires_at IS NULL
    """
    )

    print("Converting match_scores timestamps to timezone-aware...")

    op.alter_column(
        "match_scores",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )

    op.alter_column(
        "match_scores",
        "expires_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
    )

    print("Adding match_scores indexes...")

    # Check if indexes already exist before creating
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_created_at') THEN
                CREATE INDEX idx_created_at ON match_scores(created_at);
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_quality_tier') THEN
                CREATE INDEX idx_quality_tier ON match_scores(ml_quality_tier);
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_recommendation') THEN
                CREATE INDEX idx_recommendation ON match_scores(recommendation);
            END IF;
        END $$;
    """
    )

    print("Adding unique constraint on (candidate_id, job_id)...")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'uq_candidate_job_match'
            ) THEN
                ALTER TABLE match_scores 
                ADD CONSTRAINT uq_candidate_job_match 
                UNIQUE (candidate_id, job_id);
            END IF;
        END $$;
    """
    )

    print("Updating ml_models table...")

    # Fix NULL values
    op.execute(
        """
        UPDATE ml_models 
        SET deployment_date = CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
        WHERE deployment_date IS NULL
    """
    )

    op.execute(
        """
        UPDATE ml_models 
        SET is_active = TRUE
        WHERE is_active IS NULL
    """
    )

    # Alter columns
    op.alter_column(
        "ml_models",
        "training_date",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )

    op.alter_column(
        "ml_models",
        "deployment_date",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
    )

    op.alter_column(
        "ml_models",
        "retired_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )

    op.alter_column(
        "ml_models",
        "is_active",
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default=sa.text("true"),
    )

    print("Adding ml_models indexes...")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_model_active') THEN
                CREATE INDEX idx_model_active ON ml_models(is_active, deployment_date);
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_model_name_version') THEN
                CREATE INDEX idx_model_name_version ON ml_models(model_name, model_version);
            END IF;
        END $$;
    """
    )

    print("Adding ml_models unique constraint...")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'uq_model_name_version'
            ) THEN
                ALTER TABLE ml_models 
                ADD CONSTRAINT uq_model_name_version 
                UNIQUE (model_name, model_version);
            END IF;
        END $$;
    """
    )

    print("Migration complete!")


def downgrade() -> None:
    print("Downgrading schema...")

    # Drop constraints
    op.execute("ALTER TABLE ml_models DROP CONSTRAINT IF EXISTS uq_model_name_version")
    op.execute("DROP INDEX IF EXISTS idx_model_name_version")
    op.execute("DROP INDEX IF EXISTS idx_model_active")

    op.alter_column(
        "ml_models",
        "is_active",
        existing_type=sa.BOOLEAN(),
        nullable=True,
        existing_server_default=sa.text("true"),
    )

    op.alter_column(
        "ml_models",
        "retired_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )

    op.alter_column(
        "ml_models",
        "deployment_date",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
    )

    op.alter_column(
        "ml_models",
        "training_date",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )

    op.execute(
        "ALTER TABLE match_scores DROP CONSTRAINT IF EXISTS uq_candidate_job_match"
    )
    op.execute("DROP INDEX IF EXISTS idx_recommendation")
    op.execute("DROP INDEX IF EXISTS idx_quality_tier")
    op.execute("DROP INDEX IF EXISTS idx_created_at")

    op.alter_column(
        "match_scores",
        "expires_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
    )

    op.alter_column(
        "match_scores",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )

    print("Downgrade complete!")
