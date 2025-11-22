"""new_schema

Revision ID: 001_new_schema
Revises:
Create Date: 2025-11-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_new_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Drop existing enum types if they exist
    op.execute("DROP TYPE IF EXISTS enum_message_role CASCADE")
    op.execute("DROP TYPE IF EXISTS enum_order_status CASCADE")

    # Create enum types explicitly using postgresql.ENUM with create_type=False handled by table creation
    enum_order_status = postgresql.ENUM('pending', 'assigned', 'in_progress', 'completed', 'rejected', 'block', 'suspended', name='enum_order_status', create_type=True)
    enum_message_role = postgresql.ENUM('System', 'User', name='enum_message_role', create_type=True)
    enum_order_status.create(op.get_bind(), checkfirst=True)
    enum_message_role.create(op.get_bind(), checkfirst=True)

    # Create organizations table
    op.create_table('organizations',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create roles table
    op.create_table('roles',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create divisions table
    op.create_table('divisions',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'])
    )

    # Create rooms table
    op.create_table('rooms',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('room_number', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('is_booked', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'])
    )

    # Create users table
    op.create_table('users',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('mobile_phone', sa.Text(), nullable=True),
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=True),
        sa.Column('division_id', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['division_id'], ['divisions.id'])
    )

    # Create checkin_rooms table
    op.create_table('checkin_rooms',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('room_id', postgresql.ARRAY(sa.UUID()), nullable=True),
        sa.Column('checkin_date', sa.Date(), nullable=True),
        sa.Column('checkin_time', sa.Time(), nullable=True),
        sa.Column('checkout_date', sa.Date(), nullable=True),
        sa.Column('checkout_time', sa.Time(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'])
    )

    # Create orders table
    op.create_table('orders',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('order_number', sa.Text(), nullable=False),
        sa.Column('checkin_id', sa.UUID(), nullable=True),
        sa.Column('org_id', sa.UUID(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'assigned', 'in_progress', 'completed', 'rejected', 'block', 'suspended', name='enum_order_status', create_type=False), server_default='pending', nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number'),
        sa.ForeignKeyConstraint(['checkin_id'], ['checkin_rooms.id']),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'])
    )

    # Create sessions table
    op.create_table('sessions',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('start', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('end', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('duration', sa.BigInteger(), nullable=True),
        sa.Column('session_id', sa.UUID(), nullable=True),
        sa.Column('checkin_room_id', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['users.id']),
        sa.ForeignKeyConstraint(['checkin_room_id'], ['checkin_rooms.id'])
    )

    # Create messages table
    op.create_table('messages',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=True),
        sa.Column('role', postgresql.ENUM('System', 'User', name='enum_message_role', create_type=False), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'])
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('messages')
    op.drop_table('sessions')
    op.drop_table('orders')
    op.drop_table('checkin_rooms')
    op.drop_table('users')
    op.drop_table('rooms')
    op.drop_table('divisions')
    op.drop_table('roles')
    op.drop_table('organizations')

    # Drop enum types
    op.execute("DROP TYPE enum_order_status")
    op.execute("DROP TYPE enum_message_role")
