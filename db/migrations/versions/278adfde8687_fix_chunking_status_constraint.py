"""fix chunking status constraint

Revision ID: 278adfde8687
Revises: 56b08d067797
Create Date: 2026-09-30 09:33:09.802970

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '278adfde8687'
down_revision: Union[str, Sequence[str], None] = '56b08d067797'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('videos') as batch_op:
        batch_op.alter_column(
            'chunking_status',
            existing_type=sa.Enum('PENDING', 'DONE', name='chunkingstatusenum'),
            type_=sa.Enum('PENDING', 'CHUNKED', 'DONE', name='chunkingstatusenum', create_constraint=True),
            existing_nullable=False,
            existing_server_default='PENDING',
        )


def downgrade() -> None:
    with op.batch_alter_table('videos') as batch_op:
        batch_op.alter_column(
            'chunking_status',
            existing_type=sa.Enum('PENDING', 'CHUNKED', 'DONE', name='chunkingstatusenum'),
            type_=sa.Enum('PENDING', 'DONE', name='chunkingstatusenum', create_constraint=True),
            existing_nullable=False,
            existing_server_default='PENDING',
        )
