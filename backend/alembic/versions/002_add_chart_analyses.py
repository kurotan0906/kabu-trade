"""add chart_analyses table

Revision ID: 002_add_chart_analyses
Revises: 001_initial
Create Date: 2026-04-05 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_add_chart_analyses'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chart_analyses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID'),
        sa.Column('symbol', sa.String(length=10), nullable=False, comment='銘柄コード'),
        sa.Column('timeframe', sa.String(length=10), nullable=False, comment='時間足'),
        sa.Column('screenshot_path', sa.String(length=500), nullable=True, comment='スクリーンショットパス'),
        sa.Column('trend', sa.String(length=20), nullable=False, comment='トレンド'),
        sa.Column('signals', sa.JSON(), nullable=True, comment='シグナル詳細'),
        sa.Column('summary', sa.Text(), nullable=False, comment='サマリー'),
        sa.Column('recommendation', sa.String(length=10), nullable=False, comment='推奨'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='作成日時'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_chart_analyses_symbol'), 'chart_analyses', ['symbol'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_chart_analyses_symbol'), table_name='chart_analyses')
    op.drop_table('chart_analyses')
