"""Add last_logout_at field to users table

Revision ID: b13ce9a40aa2
Revises: c3e2ace1f739
Create Date: 2025-08-24 00:35:02.947548

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b13ce9a40aa2'
down_revision = 'c3e2ace1f739'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_logout_at column to users table
    op.add_column('users', sa.Column('last_logout_at', sa.DateTime(), nullable=True))
    op.create_index('ix_users_last_logout_at', 'users', ['last_logout_at'])


def downgrade() -> None:
    # Remove last_logout_at column from users table
    op.drop_index('ix_users_last_logout_at', 'users')
    op.drop_column('users', 'last_logout_at')