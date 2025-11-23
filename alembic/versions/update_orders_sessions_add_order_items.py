"""update_orders_sessions_add_order_items

Revision ID: a1b2c3d4e5f6
Revises: 17614e3551db
Create Date: 2025-01-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '17614e3551db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create new enum types
    enum_order_category = postgresql.ENUM(
        'housekeeping', 'room_service', 'maintenance', 'concierge',
        name='enum_order_category',
        create_type=True
    )
    enum_session_status = postgresql.ENUM(
        'open', 'terminated',
        name='enum_session_status',
        create_type=True
    )
    enum_session_mode = postgresql.ENUM(
        'agent', 'manual',
        name='enum_session_mode',
        create_type=True
    )

    enum_order_category.create(op.get_bind(), checkfirst=True)
    enum_session_status.create(op.get_bind(), checkfirst=True)
    enum_session_mode.create(op.get_bind(), checkfirst=True)

    # Create order_items table
    op.create_table('order_items',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('order_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('qty', sa.Integer(), nullable=True),
        sa.Column('price', sa.Float(), nullable=True, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'])
    )

    # Modify checkin_rooms table: change room_id from ARRAY to UUID
    # First, create a temporary column to store the first room_id
    op.add_column('checkin_rooms', sa.Column('room_id_new', sa.UUID(), nullable=True))

    # Migrate data: take the first room_id from the array
    op.execute("""
        UPDATE checkin_rooms
        SET room_id_new = room_id[1]
        WHERE room_id IS NOT NULL AND array_length(room_id, 1) > 0
    """)

    # Drop the old column and rename the new one
    op.drop_column('checkin_rooms', 'room_id')
    op.alter_column('checkin_rooms', 'room_id_new', new_column_name='room_id')

    # Modify sessions table: remove is_active, add status and mode
    op.drop_column('sessions', 'is_active')
    op.add_column('sessions', sa.Column(
        'status',
        postgresql.ENUM('open', 'terminated', name='enum_session_status', create_type=False),
        server_default='open',
        nullable=True
    ))
    op.add_column('sessions', sa.Column(
        'mode',
        postgresql.ENUM('agent', 'manual', name='enum_session_mode', create_type=False),
        server_default='agent',
        nullable=True
    ))

    # Modify orders table: remove checkin_id, title, description; add session_id, guest_id, total_amount; change category to enum
    # First, we need to migrate data from orders to order_items
    # This is a data migration: create order_items from existing title/description
    op.execute("""
        INSERT INTO order_items (id, order_id, title, description, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            id,
            title,
            description,
            created_at,
            updated_at
        FROM orders
        WHERE title IS NOT NULL OR description IS NOT NULL
    """)

    # Add new columns to orders
    op.add_column('orders', sa.Column('session_id', sa.UUID(), nullable=True))
    op.add_column('orders', sa.Column('guest_id', sa.UUID(), nullable=True))
    op.add_column('orders', sa.Column('total_amount', sa.Float(), nullable=True, server_default='0'))

    # Migrate data: get session_id and guest_id from checkin_rooms -> sessions -> users
    # Use a subquery with LIMIT 1 to get the first matching session
    op.execute("""
        UPDATE orders o
        SET
            session_id = (
                SELECT s.id
                FROM sessions s
                WHERE s.checkin_room_id = o.checkin_id
                  AND s.deleted_at IS NULL
                ORDER BY s.created_at DESC
                LIMIT 1
            ),
            guest_id = (
                SELECT s.session_id
                FROM sessions s
                WHERE s.checkin_room_id = o.checkin_id
                  AND s.deleted_at IS NULL
                ORDER BY s.created_at DESC
                LIMIT 1
            )
        WHERE o.checkin_id IS NOT NULL
    """)

    # Change category to enum (first update values to match enum)
    # Map 'restaurant' to 'room_service', and set default for any other unknown values
    op.execute("""
        UPDATE orders
        SET category = CASE
            WHEN category = 'restaurant' THEN 'room_service'
            WHEN category IN ('housekeeping', 'room_service', 'maintenance', 'concierge') THEN category
            ELSE 'housekeeping'
        END
        WHERE category IS NOT NULL
    """)

    # Set default for NULL categories
    op.execute("""
        UPDATE orders
        SET category = 'housekeeping'
        WHERE category IS NULL
    """)

    # Drop old columns and constraints
    op.drop_constraint('orders_checkin_id_fkey', 'orders', type_='foreignkey')
    op.drop_column('orders', 'checkin_id')
    op.drop_column('orders', 'title')
    op.drop_column('orders', 'description')

    # Add foreign key constraints for new columns (nullable since migration might leave some NULL)
    op.create_foreign_key('orders_session_id_fkey', 'orders', 'sessions', ['session_id'], ['id'])
    op.create_foreign_key('orders_guest_id_fkey', 'orders', 'users', ['guest_id'], ['id'])

    # Change category column to enum
    # Store the old category values temporarily
    op.add_column('orders', sa.Column('category_old', sa.String(), nullable=True))
    op.execute("UPDATE orders SET category_old = category")

    # Drop the old category column
    op.drop_column('orders', 'category')

    # Add new category column with enum type
    op.add_column('orders', sa.Column(
        'category',
        postgresql.ENUM('housekeeping', 'room_service', 'maintenance', 'concierge', name='enum_order_category', create_type=False),
        nullable=False,
        server_default='housekeeping'
    ))

    # Copy data from old to new, ensuring valid enum values
    op.execute("""
        UPDATE orders
        SET category = CASE
            WHEN category_old = 'restaurant' THEN 'room_service'::enum_order_category
            WHEN category_old = 'housekeeping' THEN 'housekeeping'::enum_order_category
            WHEN category_old = 'room_service' THEN 'room_service'::enum_order_category
            WHEN category_old = 'maintenance' THEN 'maintenance'::enum_order_category
            WHEN category_old = 'concierge' THEN 'concierge'::enum_order_category
            ELSE 'housekeeping'::enum_order_category
        END
    """)

    # Drop temporary column
    op.drop_column('orders', 'category_old')


def downgrade() -> None:
    """Downgrade schema."""

    # Revert orders table changes
    op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS category")
    op.add_column('orders', sa.Column('category', sa.String(), nullable=False))
    op.add_column('orders', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('title', sa.String(), nullable=False))
    op.add_column('orders', sa.Column('checkin_id', sa.UUID(), nullable=True))

    op.drop_constraint('orders_guest_id_fkey', 'orders', type_='foreignkey')
    op.drop_constraint('orders_session_id_fkey', 'orders', type_='foreignkey')
    op.create_foreign_key('orders_checkin_id_fkey', 'orders', 'checkin_rooms', ['checkin_id'], ['id'])

    op.drop_column('orders', 'total_amount')
    op.drop_column('orders', 'guest_id')
    op.drop_column('orders', 'session_id')

    # Revert sessions table changes
    op.drop_column('sessions', 'mode')
    op.drop_column('sessions', 'status')
    op.add_column('sessions', sa.Column('is_active', sa.Boolean(), nullable=True))

    # Revert checkin_rooms table changes
    # Convert single UUID back to array
    op.add_column('checkin_rooms', sa.Column('room_id_array', postgresql.ARRAY(sa.UUID()), nullable=True))
    op.execute("""
        UPDATE checkin_rooms
        SET room_id_array = ARRAY[room_id]
        WHERE room_id IS NOT NULL
    """)
    op.drop_column('checkin_rooms', 'room_id')
    op.alter_column('checkin_rooms', 'room_id_array', new_column_name='room_id')

    # Drop order_items table
    op.drop_table('order_items')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS enum_session_mode")
    op.execute("DROP TYPE IF EXISTS enum_session_status")
    op.execute("DROP TYPE IF EXISTS enum_order_category")
