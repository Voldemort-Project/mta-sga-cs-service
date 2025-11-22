"""add_user_id_to_checkin_rooms

Revision ID: 17614e3551db
Revises: f5b1f47cf870
Create Date: 2025-01-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '17614e3551db'
down_revision: Union[str, Sequence[str], None] = 'f5b1f47cf870'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add user_id column to checkin_rooms table
    op.add_column('checkin_rooms', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_checkin_rooms_user_id',
        'checkin_rooms',
        'users',
        ['user_id'],
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraint
    op.drop_constraint('fk_checkin_rooms_user_id', 'checkin_rooms', type_='foreignkey')

    # Drop user_id column
    op.drop_column('checkin_rooms', 'user_id')
