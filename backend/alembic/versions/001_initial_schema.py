"""initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create stocks table
    op.create_table(
        'stocks',
        sa.Column('code', sa.String(length=10), nullable=False, comment='銘柄コード'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='銘柄名'),
        sa.Column('sector', sa.String(length=100), nullable=True, comment='業種'),
        sa.Column('market_cap', sa.BigInteger(), nullable=True, comment='時価総額'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='作成日時'),
        sa.PrimaryKeyConstraint('code')
    )
    op.create_index(op.f('ix_stocks_code'), 'stocks', ['code'], unique=False)

    # Create stock_prices table
    op.create_table(
        'stock_prices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID'),
        sa.Column('stock_code', sa.String(length=10), nullable=False, comment='銘柄コード'),
        sa.Column('date', sa.Date(), nullable=False, comment='日付'),
        sa.Column('open', sa.Numeric(precision=10, scale=2), nullable=False, comment='始値'),
        sa.Column('high', sa.Numeric(precision=10, scale=2), nullable=False, comment='高値'),
        sa.Column('low', sa.Numeric(precision=10, scale=2), nullable=False, comment='安値'),
        sa.Column('close', sa.Numeric(precision=10, scale=2), nullable=False, comment='終値'),
        sa.Column('volume', sa.BigInteger(), nullable=False, comment='出来高'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='作成日時'),
        sa.ForeignKeyConstraint(['stock_code'], ['stocks.code'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_code', 'date', name='uq_stock_price_code_date')
    )
    op.create_index(op.f('ix_stock_prices_stock_code'), 'stock_prices', ['stock_code'], unique=False)
    op.create_index(op.f('ix_stock_prices_date'), 'stock_prices', ['date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_stock_prices_date'), table_name='stock_prices')
    op.drop_index(op.f('ix_stock_prices_stock_code'), table_name='stock_prices')
    op.drop_table('stock_prices')
    op.drop_index(op.f('ix_stocks_code'), table_name='stocks')
    op.drop_table('stocks')
