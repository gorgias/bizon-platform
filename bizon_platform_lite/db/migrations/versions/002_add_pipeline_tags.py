"""Add tags field to pipelines table.

Revision ID: 002
Revises: 001
Create Date: 2026-01-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pipelines",
        sa.Column("tags", postgresql.ARRAY(sa.String(50)), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pipelines", "tags")
