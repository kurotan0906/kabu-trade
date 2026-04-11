"""add simulation_histories table

Revision ID: 006_add_simulation_history
Revises: 005_add_portfolio
Create Date: 2026-04-11 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '006_add_simulation_history'
down_revision: Union[str, None] = '005_add_portfolio'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'simulation_histories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('input_json', sa.JSON(), nullable=False),
        sa.Column('result_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('simulation_histories')
