"""create_order_assigners_table

Revision ID: 456a55de0ffa
Revises: 61997bf04f55
Create Date: 2025-12-01 23:12:02.969647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '456a55de0ffa'
down_revision: Union[str, Sequence[str], None] = '61997bf04f55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type for order assigner status
    enum_order_assigner_status = postgresql.ENUM(
        'assigned', 'pick_up', 'in_progress', 'cancel', 'completed',
        name='enum_order_assigner_status',
        create_type=True
    )
    enum_order_assigner_status.create(op.get_bind(), checkfirst=True)

    # Create order_assigners table
    op.create_table(
        'order_assigners',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('worker_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', postgresql.ENUM('assigned', 'pick_up', 'in_progress', 'cancel', 'completed',
                                            name='enum_order_assigner_status', create_type=False),
                  server_default='assigned', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name='fk_order_assigners_order_id'),
        sa.ForeignKeyConstraint(['worker_id'], ['users.id'], name='fk_order_assigners_worker_id'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop order_assigners table
    op.drop_table('order_assigners')

    # Drop enum type
    op.execute('DROP TYPE IF EXISTS enum_order_assigner_status')
