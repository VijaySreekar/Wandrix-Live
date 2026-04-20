"""add brochure snapshots

Revision ID: 2b7e8a9c4d1f
Revises: 1a2b3c4d5e6f
Create Date: 2026-04-20 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2b7e8a9c4d1f"
down_revision: Union[str, Sequence[str], None] = "1a2b3c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SET LOCAL statement_timeout = 0")
    op.create_table(
        "brochure_snapshots",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("trip_id", sa.String(length=80), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("hero_image", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trip_id", "version_number", name="uq_brochure_snapshots_trip_version"),
    )
    op.create_index(op.f("ix_brochure_snapshots_trip_id"), "brochure_snapshots", ["trip_id"], unique=False)


def downgrade() -> None:
    op.execute("SET LOCAL statement_timeout = 0")
    op.drop_index(op.f("ix_brochure_snapshots_trip_id"), table_name="brochure_snapshots")
    op.drop_table("brochure_snapshots")
