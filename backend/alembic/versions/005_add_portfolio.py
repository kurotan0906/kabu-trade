"""add portfolio tables

Revision ID: 005_add_portfolio
Revises: 004_add_tradingview_signals
Create Date: 2026-04-11 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005_add_portfolio'
down_revision: Union[str, None] = '004_add_tradingview_signals'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'holdings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_price', sa.Float(), nullable=False, server_default='0'),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('account_type', sa.String(length=20), nullable=False, server_default='general'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_holdings_symbol'), 'holdings', ['symbol'], unique=False)

    op.create_table(
        'portfolio_settings',
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('key'),
    )

    op.create_table(
        'trade_histories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('action', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('account_type', sa.String(length=20), nullable=False, server_default='general'),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_trade_histories_symbol'), 'trade_histories', ['symbol'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_trade_histories_symbol'), table_name='trade_histories')
    op.drop_table('trade_histories')
    op.drop_table('portfolio_settings')
    op.drop_index(op.f('ix_holdings_symbol'), table_name='holdings')
    op.drop_table('holdings')
