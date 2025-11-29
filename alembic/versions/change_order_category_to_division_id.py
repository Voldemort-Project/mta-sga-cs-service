"""change_order_category_to_division_id

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a1b2
Create Date: 2025-11-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add division_id column to orders table
    op.add_column('orders', sa.Column('division_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_orders_division_id',
        'orders',
        'divisions',
        ['division_id'],
        ['id']
    )

    # Drop the category column (enum)
    op.drop_column('orders', 'category')

    # Drop the enum type if it exists (optional, but cleaner)
    # Note: This will only work if no other tables use this enum
    op.execute('DROP TYPE IF EXISTS enum_order_category')


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate the enum type
    op.execute("""
        CREATE TYPE enum_order_category AS ENUM (
            'housekeeping',
            'room_service',
            'maintenance',
            'concierge'
        )
    """)

    # Add back category column
    op.add_column('orders', sa.Column('category',
        sa.Enum('housekeeping', 'room_service', 'maintenance', 'concierge',
                name='enum_order_category'),
        nullable=False))

    # Drop foreign key constraint
    op.drop_constraint('fk_orders_division_id', 'orders', type_='foreignkey')

    # Drop division_id column
    op.drop_column('orders', 'division_id')
