"""create jobs and analysis_results tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def _enum_exists(conn, name: str) -> bool:
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = :name"),
        {"name": name},
    )
    return result.scalar() is not None


def _table_exists(conn, name: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name=:name"
        ),
        {"name": name},
    )
    return result.scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # Create enum type only if it doesn't already exist
    if not _enum_exists(conn, "jobstatus"):
        op.execute(
            "CREATE TYPE jobstatus AS ENUM "
            "('pending','processing','completed','failed')"
        )

    # Create jobs table only if it doesn't already exist
    if not _table_exists(conn, "jobs"):
        op.create_table(
            "jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "status",
                sa.Enum(
                    "pending", "processing", "completed", "failed",
                    name="jobstatus", create_type=False,
                ),
                nullable=False,
                server_default="pending",
            ),
            sa.Column("resume_filename", sa.String(512), nullable=False),
            sa.Column("jd_filename", sa.String(512), nullable=False),
            sa.Column("resume_path", sa.String(1024), nullable=True),
            sa.Column("jd_path", sa.String(1024), nullable=True),
            sa.Column("failure_reason", sa.String(2048), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
        op.create_index("ix_jobs_status", "jobs", ["status"])

    # Create analysis_results table only if it doesn't already exist
    if not _table_exists(conn, "analysis_results"):
        op.create_table(
            "analysis_results",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "job_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("jobs.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("ats_score", sa.Integer(), nullable=False),
            sa.Column("band", sa.String(16), nullable=False),
            sa.Column("hybrid_similarity", sa.Float(), nullable=False),
            sa.Column("section_scores", postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("skill_gap", postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("suggestions", postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("keyword_density", sa.Float(), nullable=True),
            sa.Column("skill_coverage", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_analysis_results_job_id", "analysis_results", ["job_id"])
        op.create_index("ix_analysis_results_user_id", "analysis_results", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_analysis_results_user_id", table_name="analysis_results")
    op.drop_index("ix_analysis_results_job_id", table_name="analysis_results")
    op.drop_table("analysis_results")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_user_id", table_name="jobs")
    op.drop_table("jobs")
    op.execute("DROP TYPE IF EXISTS jobstatus")
