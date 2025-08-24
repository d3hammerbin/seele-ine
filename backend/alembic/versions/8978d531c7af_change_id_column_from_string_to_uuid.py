"""change_id_column_from_string_to_uuid

Revision ID: 8978d531c7af
Revises: b13ce9a40aa2
Create Date: 2025-08-24 09:05:43.137396

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8978d531c7af'
down_revision = 'b13ce9a40aa2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable uuid-ossp extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Convert id columns from VARCHAR(36) to UUID
    tables_with_id = [
        'users', 'applications', 'credentials', 'processing_jobs', 'billing'
    ]
    
    for table_name in tables_with_id:
        # Change column type from VARCHAR to UUID using USING clause
        op.alter_column(table_name, 'id',
                       existing_type=sa.String(length=36),
                       type_=postgresql.UUID(as_uuid=True),
                       existing_nullable=False,
                       postgresql_using='id::uuid')
    
    # Convert foreign key columns from VARCHAR(36) to UUID
    foreign_key_updates = [
        ('applications', 'user_id'),
        ('applications', 'approved_by'),
        ('applications', 'suspended_by'),
        ('billing', 'user_id'),
        ('billing', 'application_id'),
        ('credentials', 'user_id'),
        ('processing_jobs', 'credential_id'),
        ('processing_jobs', 'user_id'),
        ('processing_jobs', 'application_id')
    ]
    
    for table_name, column_name in foreign_key_updates:
        # Change column type using USING clause
        nullable = column_name in ['approved_by', 'suspended_by']
        op.alter_column(table_name, column_name,
                       existing_type=sa.String(length=36),
                       type_=postgresql.UUID(as_uuid=True),
                       existing_nullable=nullable,
                       postgresql_using=f'{column_name}::uuid')


def downgrade() -> None:
    # Convert UUID columns back to VARCHAR(36)
    tables_with_id = [
        'users', 'applications', 'credentials', 'processing_jobs', 'billing'
    ]
    
    for table_name in tables_with_id:
        op.alter_column(table_name, 'id',
                       existing_type=postgresql.UUID(as_uuid=True),
                       type_=sa.String(length=36),
                       existing_nullable=False,
                       postgresql_using='id::text')
    
    # Convert foreign key columns back to VARCHAR(36)
    foreign_key_updates = [
        ('applications', 'user_id'),
        ('applications', 'approved_by'),
        ('applications', 'suspended_by'),
        ('billing', 'user_id'),
        ('billing', 'application_id'),
        ('credentials', 'user_id'),
        ('processing_jobs', 'credential_id'),
        ('processing_jobs', 'user_id'),
        ('processing_jobs', 'application_id')
    ]
    
    for table_name, column_name in foreign_key_updates:
        nullable = column_name in ['approved_by', 'suspended_by']
        op.alter_column(table_name, column_name,
                       existing_type=postgresql.UUID(as_uuid=True),
                       type_=sa.String(length=36),
                       existing_nullable=nullable,
                       postgresql_using=f'{column_name}::text')