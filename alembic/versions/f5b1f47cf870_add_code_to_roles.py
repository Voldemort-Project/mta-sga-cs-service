"""add_code_to_roles

Revision ID: f5b1f47cf870
Revises: 001_new_schema
Create Date: 2025-11-22 09:43:28.975813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5b1f47cf870'
down_revision: Union[str, Sequence[str], None] = '001_new_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add code column to roles table
    op.add_column('roles', sa.Column('code', sa.String(), nullable=True))

    # Create unique constraint on code
    op.create_unique_constraint('uq_roles_code', 'roles', ['code'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop unique constraint
    op.drop_constraint('uq_roles_code', 'roles', type_='unique')

    # Drop code column
    op.drop_column('roles', 'code')
