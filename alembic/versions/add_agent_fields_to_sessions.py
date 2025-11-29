"""add_agent_fields_to_sessions

Revision ID: add_agent_fields
Revises: d5e6f7a8b9c0
Create Date: 2025-11-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_agent_fields'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add agent_created column to sessions table
    op.add_column('sessions', sa.Column('agent_created', sa.Boolean(), nullable=False, server_default='false'))

    # Add category column to sessions table
    op.add_column('sessions', sa.Column('category', sa.String(50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop category column
    op.drop_column('sessions', 'category')

    # Drop agent_created column
    op.drop_column('sessions', 'agent_created')
