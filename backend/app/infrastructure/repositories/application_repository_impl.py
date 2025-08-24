#!/usr/bin/env python3
"""
Application Repository Implementation

SQLAlchemy implementation of the ApplicationRepository interface.
Handles database operations for application entities.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.repositories.application_repository import ApplicationRepository
from ...domain.entities.application import Application, ApplicationStatus, ApplicationTier, APIKeyStatus
from ...core.exceptions.base import RepositoryError, NotFoundError
from ..database.models.application import ApplicationModel


class ApplicationRepositoryImpl(ApplicationRepository):
    """
    SQLAlchemy implementation of ApplicationRepository.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, application: Application) -> Application:
        """Create a new application in the database."""
        try:
            # Convert domain entity to database model
            app_model = ApplicationModel.from_domain_entity(application)
            
            # Add to session and commit
            self._session.add(app_model)
            await self._session.commit()
            await self._session.refresh(app_model)
            
            # Convert back to domain entity
            return app_model.to_domain_entity()
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to create application: {str(e)}")
    
    async def get_by_id(self, application_id: UUID) -> Optional[Application]:
        """Get application by ID."""
        try:
            stmt = select(ApplicationModel).where(ApplicationModel.id == application_id)
            result = await self._session.execute(stmt)
            app_model = result.scalar_one_or_none()
            
            return app_model.to_domain_entity() if app_model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to get application by ID: {str(e)}")
    
    async def get_by_user_id(
        self, 
        user_id: UUID, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Application]:
        """Get applications for a specific user."""
        try:
            stmt = (
                select(ApplicationModel)
                .where(ApplicationModel.user_id == user_id)
                .offset(offset)
                .limit(limit)
                .order_by(ApplicationModel.created_at.desc())
            )
            result = await self._session.execute(stmt)
            app_models = result.scalars().all()
            
            return [app_model.to_domain_entity() for app_model in app_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get applications by user ID: {str(e)}")
    
    async def get_by_client_key(self, client_key: str) -> Optional[Application]:
        """Get application by client key."""
        try:
            # Client key is stored in the api_keys JSONB field
            # We need to search within the JSON structure
            stmt = select(ApplicationModel).where(
                ApplicationModel.api_keys.op('@>')([{"client_key": client_key}])
            )
            result = await self._session.execute(stmt)
            app_model = result.scalar_one_or_none()
            
            return app_model.to_domain_entity() if app_model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to get application by client key: {str(e)}")
    
    async def get_by_name(self, name: str, user_id: UUID) -> Optional[Application]:
        """Get application by name for a specific user."""
        try:
            stmt = select(ApplicationModel).where(
                and_(
                    ApplicationModel.name == name,
                    ApplicationModel.user_id == user_id
                )
            )
            result = await self._session.execute(stmt)
            app_model = result.scalar_one_or_none()
            
            return app_model.to_domain_entity() if app_model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to get application by name: {str(e)}")
    
    async def list_applications(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[ApplicationStatus] = None,
        tier: Optional[ApplicationTier] = None,
        user_id: Optional[UUID] = None
    ) -> List[Application]:
        """List applications with optional filters."""
        try:
            stmt = select(ApplicationModel)
            
            # Apply filters
            if status:
                stmt = stmt.where(ApplicationModel.status == status)
            if tier:
                stmt = stmt.where(ApplicationModel.tier == tier)
            if user_id:
                stmt = stmt.where(ApplicationModel.user_id == user_id)
            
            # Apply pagination
            stmt = stmt.offset(offset).limit(limit)
            stmt = stmt.order_by(ApplicationModel.created_at.desc())
            
            result = await self._session.execute(stmt)
            app_models = result.scalars().all()
            
            return [app_model.to_domain_entity() for app_model in app_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to list applications: {str(e)}")
    
    async def update(self, application: Application) -> Application:
        """Update an existing application."""
        try:
            # Get existing application model
            stmt = select(ApplicationModel).where(ApplicationModel.id == application.id)
            result = await self._session.execute(stmt)
            app_model = result.scalar_one_or_none()
            
            if not app_model:
                raise NotFoundError(f"Application with ID {application.id} not found")
            
            # Update fields from domain entity
            app_model.name = application.name
            app_model.description = application.description
            app_model.website_url = application.website_url
            app_model.callback_url = application.callback_url
            app_model.status = application.status
            app_model.tier = application.tier
            app_model.webhook_url = application.webhook_url
            app_model.webhook_secret = application.webhook_secret
            app_model.allowed_origins = application.allowed_origins
            app_model.approved_at = application.approved_at
            app_model.suspended_at = application.suspended_at
            app_model.updated_at = datetime.utcnow()
            app_model.extra_metadata = application.metadata
            
            # Update limits
            limits_dict = {
                'requests_per_minute': application.limits.requests_per_minute,
                'requests_per_hour': application.limits.requests_per_hour,
                'requests_per_day': application.limits.requests_per_day,
                'requests_per_month': application.limits.requests_per_month,
                'max_file_size_mb': application.limits.max_file_size_mb,
                'max_concurrent_jobs': application.limits.max_concurrent_jobs,
                'allowed_file_types': application.limits.allowed_file_types,
                'webhook_enabled': application.limits.webhook_enabled,
                'priority_processing': application.limits.priority_processing
            }
            app_model.limits = limits_dict
            
            # Update API keys
            api_keys_list = []
            for api_key in application.api_keys:
                key_dict = {
                    'key_id': str(api_key.key_id),
                    'client_key': api_key.client_key,
                    'key_hash': api_key.key_hash,
                    'name': api_key.name,
                    'status': api_key.status.value,
                    'created_at': api_key.created_at.isoformat(),
                    'last_used_at': api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                    'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
                    'permissions': api_key.permissions,
                    'metadata': api_key.metadata
                }
                api_keys_list.append(key_dict)
            app_model.api_keys = api_keys_list
            
            # Update stats
            stats_dict = {
                'total_requests': application.stats.total_requests,
                'successful_requests': application.stats.successful_requests,
                'failed_requests': application.stats.failed_requests,
                'total_processing_time_seconds': float(application.stats.total_processing_time_seconds),
                'average_processing_time_seconds': float(application.stats.average_processing_time_seconds),
                'total_cost_usd': float(application.stats.total_cost_usd),
                'last_request_at': application.stats.last_request_at.isoformat() if application.stats.last_request_at else None,
                'requests_today': application.stats.requests_today,
                'requests_this_month': application.stats.requests_this_month,
                'error_rate_percentage': float(application.stats.error_rate_percentage)
            }
            app_model.stats = stats_dict
            
            await self._session.commit()
            await self._session.refresh(app_model)
            
            return app_model.to_domain_entity()
            
        except NotFoundError:
            raise
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to update application: {str(e)}")
    
    async def delete(self, application_id: UUID) -> bool:
        """Soft delete an application."""
        try:
            stmt = (
                update(ApplicationModel)
                .where(ApplicationModel.id == application_id)
                .values(
                    status=ApplicationStatus.REVOKED,
                    deleted_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to delete application: {str(e)}")
    
    async def count_applications(
        self,
        status: Optional[ApplicationStatus] = None,
        tier: Optional[ApplicationTier] = None,
        user_id: Optional[UUID] = None
    ) -> int:
        """Count applications with optional filters."""
        try:
            stmt = select(func.count(ApplicationModel.id))
            
            # Apply filters
            if status:
                stmt = stmt.where(ApplicationModel.status == status)
            if tier:
                stmt = stmt.where(ApplicationModel.tier == tier)
            if user_id:
                stmt = stmt.where(ApplicationModel.user_id == user_id)
            
            result = await self._session.execute(stmt)
            return result.scalar()
            
        except Exception as e:
            raise RepositoryError(f"Failed to count applications: {str(e)}")
    
    async def search_applications(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Application]:
        """Search applications by name or description."""
        try:
            search_term = f"%{query.lower()}%"
            
            stmt = select(ApplicationModel).where(
                or_(
                    ApplicationModel.name.ilike(search_term),
                    ApplicationModel.description.ilike(search_term)
                )
            )
            
            stmt = stmt.offset(offset).limit(limit)
            stmt = stmt.order_by(ApplicationModel.created_at.desc())
            
            result = await self._session.execute(stmt)
            app_models = result.scalars().all()
            
            return [app_model.to_domain_entity() for app_model in app_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to search applications: {str(e)}")
    
    async def get_applications_by_status(self, status: ApplicationStatus) -> List[Application]:
        """Get all applications with a specific status."""
        try:
            stmt = select(ApplicationModel).where(ApplicationModel.status == status)
            result = await self._session.execute(stmt)
            app_models = result.scalars().all()
            
            return [app_model.to_domain_entity() for app_model in app_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get applications by status: {str(e)}")
    
    async def get_applications_by_tier(self, tier: ApplicationTier) -> List[Application]:
        """Get all applications with a specific tier."""
        try:
            stmt = select(ApplicationModel).where(ApplicationModel.tier == tier)
            result = await self._session.execute(stmt)
            app_models = result.scalars().all()
            
            return [app_model.to_domain_entity() for app_model in app_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get applications by tier: {str(e)}")
    
    async def update_last_used(self, application_id: UUID) -> None:
        """Update application's last used timestamp."""
        try:
            stmt = (
                update(ApplicationModel)
                .where(ApplicationModel.id == application_id)
                .values(
                    last_used_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to update last used: {str(e)}")
    
    async def increment_request_count(self, application_id: UUID) -> None:
        """Increment application's request count."""
        try:
            # This would typically update the stats in the JSONB field
            # For now, we'll update the last_api_call_at timestamp
            stmt = (
                update(ApplicationModel)
                .where(ApplicationModel.id == application_id)
                .values(
                    last_api_call_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to increment request count: {str(e)}")
    
    async def revoke_api_key(self, application_id: UUID, api_key: str) -> bool:
        """Revoke a specific API key."""
        try:
            # Get the application
            app = await self.get_by_id(application_id)
            if not app:
                return False
            
            # Find and revoke the API key
            key_found = False
            for key in app.api_keys:
                if key.client_key == api_key:
                    key.status = APIKeyStatus.REVOKED
                    key_found = True
                    break
            
            if key_found:
                await self.update(app)
                return True
            
            return False
            
        except Exception as e:
            raise RepositoryError(f"Failed to revoke API key: {str(e)}")
    
    async def get_active_applications_count(self, user_id: Optional[UUID] = None) -> int:
        """Get count of active applications."""
        try:
            stmt = select(func.count(ApplicationModel.id)).where(
                ApplicationModel.status == ApplicationStatus.ACTIVE
            )
            
            if user_id:
                stmt = stmt.where(ApplicationModel.user_id == user_id)
            
            result = await self._session.execute(stmt)
            return result.scalar()
            
        except Exception as e:
            raise RepositoryError(f"Failed to get active applications count: {str(e)}")
    
    async def bulk_update_status(
        self,
        application_ids: List[UUID],
        status: ApplicationStatus
    ) -> int:
        """Update status for multiple applications."""
        try:
            stmt = (
                update(ApplicationModel)
                .where(ApplicationModel.id.in_(application_ids))
                .values(
                    status=status,
                    updated_at=datetime.utcnow()
                )
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to bulk update status: {str(e)}")