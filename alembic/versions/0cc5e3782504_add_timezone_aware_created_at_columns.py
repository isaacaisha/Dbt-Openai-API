"""Add timezone-aware created_at columns

Revision ID: 0cc5e3782504
Revises: 40cdfcb5d376
Create Date: 2024-05-25 03:28:13.318836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cc5e3782504'
down_revision: Union[str, None] = '40cdfcb5d376'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'api_memories', 
        'created_at',
        existing_type=sa.TIMESTAMP(),
        type_=sa.TIMESTAMP(timezone=True),
        existing_nullable=False,
        server_default=sa.text('(now() at time zone \'utc\')')
    )
    op.alter_column(
        'api_users', 
        'created_at',
        existing_type=sa.TIMESTAMP(),
        type_=sa.TIMESTAMP(timezone=True),
        existing_nullable=False,
        server_default=sa.text('(now() at time zone \'utc\')')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'api_memories', 
        'created_at',
        existing_type=sa.TIMESTAMP(timezone=True),
        type_=sa.TIMESTAMP(),
        existing_nullable=False,
        server_default=None
    )
    op.alter_column(
        'api_users', 
        'created_at',
        existing_type=sa.TIMESTAMP(timezone=True),
        type_=sa.TIMESTAMP(),
        existing_nullable=False,
        server_default=None
    )
    # ### end Alembic commands ###
