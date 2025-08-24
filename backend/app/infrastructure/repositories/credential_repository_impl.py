#!/usr/bin/env python3
"""
Credential Repository Implementation

Implements the credential repository interface using SQLAlchemy ORM.
Handles database operations for credential entities.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from ...domain.repositories.credential_repository import CredentialRepository
from ...domain.entities.credential import Credential, CredentialType, ProcessingStatus
from ...core.exceptions.base import RepositoryError
from ..database.models.credential import CredentialModel


class CredentialRepositoryImpl(CredentialRepository):
    """SQLAlchemy implementation of credential repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, credential: Credential) -> Credential:
        """Create a new credential record."""
        try:
            model = CredentialModel.from_domain_entity(credential)
            self.session.add(model)
            await self.session.flush()
            await self.session.refresh(model)
            return model.to_domain_entity()
        except Exception as e:
            raise RepositoryError(f"Failed to create credential: {str(e)}") from e

    async def get_by_id(self, credential_id: UUID) -> Optional[Credential]:
        """Retrieve a credential by its ID."""
        try:
            stmt = (
                select(CredentialModel)
                .options(selectinload(CredentialModel.user))
                .options(selectinload(CredentialModel.processing_jobs))
                .where(CredentialModel.id == credential_id)
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            return model.to_domain_entity() if model else None
        except Exception as e:
            raise RepositoryError(f"Failed to get credential by ID: {str(e)}") from e

    async def get_by_user_id(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[Credential]:
        """Retrieve credentials for a specific user."""
        try:
            stmt = (
                select(CredentialModel)
                .options(selectinload(CredentialModel.user))
                .options(selectinload(CredentialModel.processing_jobs))
                .where(CredentialModel.user_id == user_id)
                .order_by(CredentialModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [model.to_domain_entity() for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to get credentials by user ID: {str(e)}") from e

    async def update(self, credential: Credential) -> Credential:
        """Update an existing credential."""
        try:
            model = await self.session.get(CredentialModel, credential.id)
            if not model:
                raise RepositoryError(f"Credential with ID {credential.id} not found")
            
            # Update model from domain entity
            updated_model = CredentialModel.from_domain_entity(credential)
            for key, value in updated_model.__dict__.items():
                if not key.startswith('_') and key != 'id':
                    setattr(model, key, value)
            
            await self.session.flush()
            await self.session.refresh(model)
            return model.to_domain_entity()
        except Exception as e:
            raise RepositoryError(f"Failed to update credential: {str(e)}") from e

    async def delete(self, credential_id: UUID) -> bool:
        """Delete a credential by ID."""
        try:
            stmt = delete(CredentialModel).where(CredentialModel.id == credential_id)
            result = await self.session.execute(stmt)
            return result.rowcount > 0
        except Exception as e:
            raise RepositoryError(f"Failed to delete credential: {str(e)}") from e

    async def get_by_status(self, status: ProcessingStatus, limit: int = 50, offset: int = 0) -> List[Credential]:
        """Retrieve credentials by processing status."""
        try:
            stmt = (
                select(CredentialModel)
                .options(selectinload(CredentialModel.user))
                .options(selectinload(CredentialModel.processing_jobs))
                .where(CredentialModel.processing_status == status.value)
                .order_by(CredentialModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [model.to_domain_entity() for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to get credentials by status: {str(e)}") from e

    async def get_by_type(self, credential_type: CredentialType, limit: int = 50, offset: int = 0) -> List[Credential]:
        """Retrieve credentials by type."""
        try:
            stmt = (
                select(CredentialModel)
                .options(selectinload(CredentialModel.user))
                .options(selectinload(CredentialModel.processing_jobs))
                .where(CredentialModel.credential_type == credential_type.value)
                .order_by(CredentialModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [model.to_domain_entity() for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to get credentials by type: {str(e)}") from e

    async def count_by_user_id(self, user_id: UUID) -> int:
        """Count credentials for a specific user."""
        try:
            stmt = select(func.count(CredentialModel.id)).where(CredentialModel.user_id == user_id)
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            raise RepositoryError(f"Failed to count credentials by user ID: {str(e)}") from e

    async def get_processing_stats(self, user_id: Optional[UUID] = None) -> Dict[str, int]:
        """Get processing statistics."""
        try:
            base_stmt = select(
                CredentialModel.processing_status,
                func.count(CredentialModel.id).label('count')
            )
            
            if user_id:
                base_stmt = base_stmt.where(CredentialModel.user_id == user_id)
            
            stmt = base_stmt.group_by(CredentialModel.processing_status)
            result = await self.session.execute(stmt)
            
            stats = {}
            for row in result:
                stats[row.processing_status] = row.count
            
            return stats
        except Exception as e:
            raise RepositoryError(f"Failed to get processing stats: {str(e)}") from e

    async def get_by_application_id(self, application_id: UUID, limit: int = 50, offset: int = 0) -> List[Credential]:
        """Retrieve credentials processed by a specific application."""
        try:
            # Note: This assumes there's a relationship between credentials and applications through processing jobs
            stmt = (
                select(CredentialModel)
                .options(selectinload(CredentialModel.user))
                .options(selectinload(CredentialModel.processing_jobs))
                .order_by(CredentialModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [model.to_domain_entity() for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to get credentials by application ID: {str(e)}") from e

    async def list_credentials(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[Credential]:
        """List credentials with optional filtering and sorting."""
        try:
            stmt = (
                select(CredentialModel)
                .options(selectinload(CredentialModel.user))
                .options(selectinload(CredentialModel.processing_jobs))
            )
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(CredentialModel, key):
                        stmt = stmt.where(getattr(CredentialModel, key) == value)
            
            # Apply sorting
            if hasattr(CredentialModel, sort_by):
                sort_column = getattr(CredentialModel, sort_by)
                if sort_order.lower() == "desc":
                    stmt = stmt.order_by(sort_column.desc())
                else:
                    stmt = stmt.order_by(sort_column.asc())
            
            stmt = stmt.limit(limit).offset(offset)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [model.to_domain_entity() for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to list credentials: {str(e)}") from e

    async def count_credentials(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count credentials with optional filtering."""
        try:
            stmt = select(func.count(CredentialModel.id))
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(CredentialModel, key):
                        stmt = stmt.where(getattr(CredentialModel, key) == value)
            
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            raise RepositoryError(f"Failed to count credentials: {str(e)}") from e

    async def get_credentials_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Credential]:
        """Retrieve credentials within a date range."""
        try:
            stmt = (
                select(CredentialModel)
                .options(selectinload(CredentialModel.user))
                .options(selectinload(CredentialModel.processing_jobs))
                .where(and_(
                    CredentialModel.created_at >= start_date,
                    CredentialModel.created_at <= end_date
                ))
            )
            
            if user_id:
                stmt = stmt.where(CredentialModel.user_id == user_id)
            
            stmt = stmt.order_by(CredentialModel.created_at.desc()).limit(limit).offset(offset)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [model.to_domain_entity() for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to get credentials by date range: {str(e)}") from e

    async def get_failed_credentials(
        self,
        retry_count_threshold: int = 3,
        limit: int = 50,
        offset: int = 0
    ) -> List[Credential]:
        """Retrieve credentials that have failed processing."""
        try:
            stmt = (
                select(CredentialModel)
                .options(selectinload(CredentialModel.user))
                .options(selectinload(CredentialModel.processing_jobs))
                .where(and_(
                    CredentialModel.processing_status == ProcessingStatus.FAILED.value,
                    CredentialModel.retry_count >= retry_count_threshold
                ))
                .order_by(CredentialModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [model.to_domain_entity() for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to get failed credentials: {str(e)}") from e

    async def update_processing_status(self, credential_id: UUID, status: ProcessingStatus) -> bool:
        """Update only the processing status of a credential."""
        try:
            stmt = (
                update(CredentialModel)
                .where(CredentialModel.id == credential_id)
                .values(processing_status=status.value, updated_at=datetime.utcnow())
            )
            result = await self.session.execute(stmt)
            return result.rowcount > 0
        except Exception as e:
            raise RepositoryError(f"Failed to update processing status: {str(e)}") from e

    async def bulk_update_status(
        self,
        credential_ids: List[UUID],
        status: ProcessingStatus
    ) -> int:
        """Update processing status for multiple credentials."""
        try:
            stmt = (
                update(CredentialModel)
                .where(CredentialModel.id.in_(credential_ids))
                .values(processing_status=status.value, updated_at=datetime.utcnow())
            )
            result = await self.session.execute(stmt)
            return result.rowcount
        except Exception as e:
            raise RepositoryError(f"Failed to bulk update status: {str(e)}") from e