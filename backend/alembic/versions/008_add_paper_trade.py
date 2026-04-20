"""add paper trade tables

Revision ID: 008_add_paper_trade
Revises: 007_add_close_price
Create Date: 2026-04-20 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '008_add_paper_trade'
down_revision: Union[str, None] = '007_add_close_price'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'paper_accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('initial_cash', sa.Float(), nullable=False),
        sa.Column('cash_balance', sa.Float(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'paper_holdings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('avg_price', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', 'symbol', name='uq_paper_holdings_account_symbol'),
    )
    op.create_index('ix_paper_holdings_account_id', 'paper_holdings', ['account_id'])
    op.create_index('ix_paper_holdings_symbol', 'paper_holdings', ['symbol'])

    op.create_table(
        'paper_trades',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('action', sa.String(length=4), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('realized_pl', sa.Float(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('fee', sa.Float(), nullable=True, comment='予約: 手数料。MVP では常に NULL'),
        sa.Column('dividend', sa.Float(), nullable=True, comment='予約: 配当。MVP では常に NULL'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_paper_trades_account_id', 'paper_trades', ['account_id'])
    op.create_index('ix_paper_trades_symbol', 'paper_trades', ['symbol'])
    op.create_index('ix_paper_trades_executed_at', 'paper_trades', ['executed_at'])


def downgrade() -> None:
    op.drop_index('ix_paper_trades_executed_at', table_name='paper_trades')
    op.drop_index('ix_paper_trades_symbol', table_name='paper_trades')
    op.drop_index('ix_paper_trades_account_id', table_name='paper_trades')
    op.drop_table('paper_trades')
    op.drop_index('ix_paper_holdings_symbol', table_name='paper_holdings')
    op.drop_index('ix_paper_holdings_account_id', table_name='paper_holdings')
    op.drop_table('paper_holdings')
    op.drop_table('paper_accounts')
