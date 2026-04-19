"""add close_price to stock_scores

Revision ID: 007_add_close_price_to_stock_scores
Revises: 006_add_simulation_history
Create Date: 2026-04-19 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '007_add_close_price'
down_revision: Union[str, None] = '006_add_simulation_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'stock_scores',
        sa.Column('close_price', sa.Float(), nullable=True, comment='終値（バッチ取得時点）'),
    )


def downgrade() -> None:
    op.drop_column('stock_scores', 'close_price')
