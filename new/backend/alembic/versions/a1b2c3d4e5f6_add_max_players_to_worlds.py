"""add max_players to worlds

Revision ID: a1b2c3d4e5f6
Revises: 180b7cdd29c3
Create Date: 2026-02-26 18:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '180b7cdd29c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('worlds', sa.Column('max_players', sa.SmallInteger(), nullable=False, server_default='20'))


def downgrade() -> None:
    op.drop_column('worlds', 'max_players')
