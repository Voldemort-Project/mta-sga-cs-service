"""add_note_to_order_items

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2025-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a1'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add note column to order_items table
    op.add_column('order_items', sa.Column('note', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove note column from order_items table
    op.drop_column('order_items', 'note')
