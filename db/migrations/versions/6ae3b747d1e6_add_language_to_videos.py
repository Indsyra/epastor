"""add language to videos

Revision ID: 6ae3b747d1e6
Revises: bd6bd160853c
Create Date: 2026-09-09 10:28:17.348109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ae3b747d1e6'
down_revision: Union[str, Sequence[str], None] = 'bd6bd160853c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('videos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('language', sa.Enum('FR', 'EN', name='languageenum', create_constraint=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('videos', schema=None) as batch_op:
        batch_op.drop_column('language')
