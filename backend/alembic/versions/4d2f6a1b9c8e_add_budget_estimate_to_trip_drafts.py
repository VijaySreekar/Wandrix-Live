"""add budget estimate to trip drafts

Revision ID: 4d2f6a1b9c8e
Revises: 3c9d8e7f6a5b
Create Date: 2026-04-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "4d2f6a1b9c8e"
down_revision: Union[str, Sequence[str], None] = "3c9d8e7f6a5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "trip_drafts",
        sa.Column("budget_estimate", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("trip_drafts", "budget_estimate")
