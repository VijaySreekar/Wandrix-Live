"""add provider usage metrics

Revision ID: 3c9d8e7f6a5b
Revises: 2b7e8a9c4d1f
Create Date: 2026-04-20 21:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3c9d8e7f6a5b"
down_revision: Union[str, Sequence[str], None] = "2b7e8a9c4d1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SET LOCAL statement_timeout = 0")
    op.create_table(
        "provider_usage_metrics",
        sa.Column("provider_key", sa.String(length=80), nullable=False),
        sa.Column("usage_month", sa.Date(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quota_limit", sa.Integer(), nullable=True),
        sa.Column("last_status", sa.String(length=24), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("provider_key", "usage_month"),
    )


def downgrade() -> None:
    op.execute("SET LOCAL statement_timeout = 0")
    op.drop_table("provider_usage_metrics")
