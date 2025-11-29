"""add_checkin_room_id_to_orders

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2025-11-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a1b2'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add checkin_room_id column to orders table
    op.add_column('orders', sa.Column('checkin_room_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_orders_checkin_room_id',
        'orders',
        'checkin_rooms',
        ['checkin_room_id'],
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraint
    op.drop_constraint('fk_orders_checkin_room_id', 'orders', type_='foreignkey')

    # Drop checkin_room_id column
    op.drop_column('orders', 'checkin_room_id')
