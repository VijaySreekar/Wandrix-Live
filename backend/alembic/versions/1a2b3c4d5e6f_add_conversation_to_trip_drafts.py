"""add conversation to trip drafts

Revision ID: 1a2b3c4d5e6f
Revises: 6974c6890f79
Create Date: 2026-04-19 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "6974c6890f79"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SET LOCAL statement_timeout = 0")
    op.add_column(
        "trip_drafts",
        sa.Column(
            "conversation",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.execute("UPDATE trip_drafts SET conversation = '{}'::jsonb WHERE conversation IS NULL")
    op.alter_column("trip_drafts", "conversation", nullable=False)


def downgrade() -> None:
    op.execute("SET LOCAL statement_timeout = 0")
    op.drop_column("trip_drafts", "conversation")
