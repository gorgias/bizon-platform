"""Add log_file_path column to pipeline_runs table.

Supports file-based log storage to reduce DB bloat from log accumulation.
Existing runs keep their logs column data for backward compatibility.

Revision ID: 003
Revises: 002
Create Date: 2026-01-18
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pipeline_runs",
        sa.Column("log_file_path", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pipeline_runs", "log_file_path")
