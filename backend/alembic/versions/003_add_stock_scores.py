"""add stock_scores table

Revision ID: 003_add_stock_scores
Revises: 002_add_chart_analyses
Create Date: 2026-04-05 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_add_stock_scores'
down_revision: Union[str, None] = '002_add_chart_analyses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'stock_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False, comment='銘柄コード'),
        sa.Column('name', sa.String(length=100), nullable=True, comment='銘柄名'),
        sa.Column('sector', sa.String(length=100), nullable=True, comment='セクター'),
        sa.Column('scored_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('rating', sa.String(length=20), nullable=True),
        sa.Column('fundamental_score', sa.Float(), nullable=True),
        sa.Column('technical_score', sa.Float(), nullable=True),
        sa.Column('kurotenko_score', sa.Float(), nullable=True),
        sa.Column('kurotenko_criteria', sa.JSON(), nullable=True),
        sa.Column('per', sa.Float(), nullable=True),
        sa.Column('pbr', sa.Float(), nullable=True),
        sa.Column('roe', sa.Float(), nullable=True),
        sa.Column('dividend_yield', sa.Float(), nullable=True),
        sa.Column('revenue_growth', sa.Float(), nullable=True),
        sa.Column('ma_score', sa.Float(), nullable=True),
        sa.Column('rsi_score', sa.Float(), nullable=True),
        sa.Column('macd_score', sa.Float(), nullable=True),
        sa.Column('data_quality', sa.String(length=20), nullable=False, server_default='ok'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_stock_scores_symbol'), 'stock_scores', ['symbol'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_stock_scores_symbol'), table_name='stock_scores')
    op.drop_table('stock_scores')
