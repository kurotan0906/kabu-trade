"""add tradingview_signals table

Revision ID: 004_add_tradingview_signals
Revises: 003_add_stock_scores
Create Date: 2026-04-05 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_add_tradingview_signals'
down_revision: Union[str, None] = '003_add_stock_scores'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tradingview_signals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False, comment='銘柄コード'),
        sa.Column('recommendation', sa.String(length=20), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('buy_count', sa.Integer(), nullable=True),
        sa.Column('sell_count', sa.Integer(), nullable=True),
        sa.Column('neutral_count', sa.Integer(), nullable=True),
        sa.Column('ma_recommendation', sa.String(length=20), nullable=True),
        sa.Column('osc_recommendation', sa.String(length=20), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tradingview_signals_symbol'), 'tradingview_signals', ['symbol'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tradingview_signals_symbol'), table_name='tradingview_signals')
    op.drop_table('tradingview_signals')
