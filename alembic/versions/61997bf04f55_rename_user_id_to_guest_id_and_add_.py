"""rename_user_id_to_guest_id_and_add_admin_id

Revision ID: 61997bf04f55
Revises: add_agent_fields
Create Date: 2025-11-29 14:07:07.940739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '61997bf04f55'
down_revision: Union[str, Sequence[str], None] = 'add_agent_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Drop the foreign key constraint on user_id
    op.drop_constraint('fk_checkin_rooms_user_id', 'checkin_rooms', type_='foreignkey')

    # Step 2: Rename user_id column to guest_id
    op.alter_column('checkin_rooms', 'user_id', new_column_name='guest_id')

    # Step 3: Add admin_id column
    op.add_column('checkin_rooms', sa.Column('admin_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Step 4: Re-create foreign key constraint for guest_id
    op.create_foreign_key(
        'fk_checkin_rooms_guest_id',
        'checkin_rooms',
        'users',
        ['guest_id'],
        ['id']
    )

    # Step 5: Add foreign key constraint for admin_id
    op.create_foreign_key(
        'fk_checkin_rooms_admin_id',
        'checkin_rooms',
        'users',
        ['admin_id'],
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Step 1: Drop foreign key constraints
    op.drop_constraint('fk_checkin_rooms_admin_id', 'checkin_rooms', type_='foreignkey')
    op.drop_constraint('fk_checkin_rooms_guest_id', 'checkin_rooms', type_='foreignkey')

    # Step 2: Drop admin_id column
    op.drop_column('checkin_rooms', 'admin_id')

    # Step 3: Rename guest_id back to user_id
    op.alter_column('checkin_rooms', 'guest_id', new_column_name='user_id')

    # Step 4: Re-create original foreign key constraint for user_id
    op.create_foreign_key(
        'fk_checkin_rooms_user_id',
        'checkin_rooms',
        'users',
        ['user_id'],
        ['id']
    )
