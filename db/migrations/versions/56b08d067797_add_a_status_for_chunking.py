"""add chunked status for chunking pipeline

Revision ID: 56b08d067797
Revises: b711a43060d7
Create Date: 2026-09-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '56b08d067797'
down_revision: Union[str, Sequence[str], None] = 'b711a43060d7'
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