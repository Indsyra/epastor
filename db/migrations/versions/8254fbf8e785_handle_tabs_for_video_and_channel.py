"""handle tabs for Video and Channel

Revision ID: 8254fbf8e785
Revises: 6ae3b747d1e6
Create Date: 2026-09-09 17:10:00.972667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8254fbf8e785'
down_revision: Union[str, Sequence[str], None] = '6ae3b747d1e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default nécessaire : channels contient déjà des lignes,
    # une colonne NOT NULL sans valeur par défaut échouerait sur SQLite
    # (testé et confirmé).
    op.add_column(
        'channels',
        sa.Column('target_tabs', sa.JSON(), nullable=False, server_default='["videos", "streams"]')
    )

    # videos est vidée avant cette migration (voir clear_videos.py) donc
    # pas de lignes existantes à gérer ici. batch_alter_table quand même
    # nécessaire pour source_tab : Enum(create_constraint=True) perd sa
    # contrainte CHECK silencieusement sans le mode batch (déjà rencontré).
    with op.batch_alter_table('videos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_tab', sa.Enum('VIDEOS', 'STREAMS', name='sourcetabenum', create_constraint=True), nullable=False))
        batch_op.add_column(sa.Column('is_excluded_by_config', sa.Boolean(), nullable=False, server_default=sa.false()))

    # NOTE : les 7 op.drop_constraint(...) générés automatiquement ont
    # été retirés — même faux positif habituel (Alembic compare mal les
    # contraintes CHECK d'Enum sur SQLite), aucune n'a réellement changé.


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('videos', schema=None) as batch_op:
        batch_op.drop_column('is_excluded_by_config')
        batch_op.drop_column('source_tab')

    op.drop_column('channels', 'target_tabs')