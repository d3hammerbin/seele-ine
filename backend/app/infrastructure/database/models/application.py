#!/usr/bin/env python3
"""
Application Database Model

SQLAlchemy model for API-consuming application data persistence.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship

from ..base import BaseModel
from ....domain.entities.application import (
    ApplicationStatus, ApplicationTier, APIKeyStatus
)


class ApplicationModel(BaseModel):
    """Application database model."""
    
    __tablename__ = "applications"
    
    # Foreign key to user
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic application information
    name = Column(
        String(100),
        nullable=False
    )
    
    description = Column(
        Text,
        nullable=True
    )
    
    status = Column(
        SQLEnum(ApplicationStatus),
        nullable=False,
        default=ApplicationStatus.PENDING_APPROVAL,
        index=True
    )
    
    tier = Column(
        SQLEnum(ApplicationTier),
        nullable=False,
        default=ApplicationTier.DEVELOPMENT,
        index=True
    )
    
    # Application URLs and contact
    website_url = Column(
        String(500),
        nullable=True
    )
    
    callback_url = Column(
        String(500),
        nullable=True
    )
    
    contact_email = Column(
        String(255),
        nullable=True
    )
    
    # API Keys (stored as JSON array)
    api_keys = Column(
        JSON,
        nullable=False,
        default=list
    )
    
    # Application limits (stored as JSON)
    limits = Column(
        JSON,
        nullable=False,
        default=dict
    )
    
    # Usage statistics (stored as JSON)
    stats = Column(
        JSON,
        nullable=False,
        default=dict
    )
    
    # Approval information
    approved_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    approved_by = Column(
        String(36),
        nullable=True
    )
    
    approval_notes = Column(
        Text,
        nullable=True
    )
    
    # Suspension information
    suspended_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    suspended_by = Column(
        String(36),
        nullable=True
    )
    
    suspension_reason = Column(
        Text,
        nullable=True
    )
    
    # Last activity tracking
    last_used_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    last_api_call_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    # Soft delete
    deleted_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    # Additional metadata
    extra_metadata = Column(
        JSON,
        nullable=False,
        default=dict
    )
    
    # Relationships
    user = relationship(
        "UserModel",
        back_populates="applications"
    )
    
    processing_jobs = relationship(
        "ProcessingJobModel",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    billing_records = relationship(
        "BillingModel",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def to_domain_entity(self):
        """Convert database model to domain entity.
        
        Returns:
            Application domain entity
        """
        from ....domain.entities.application import (
            Application, APIKey, ApplicationLimits, ApplicationStats
        )
        
        # Convert API keys
        api_keys_list = []
        for key_data in self.api_keys or []:
            api_key = APIKey(
                key_id=key_data['key_id'],
                key_hash=key_data['key_hash'],
                name=key_data['name'],
                status=APIKeyStatus(key_data['status']),
                created_at=datetime.fromisoformat(key_data['created_at']),
                last_used_at=datetime.fromisoformat(key_data['last_used_at']) if key_data.get('last_used_at') else None,
                expires_at=datetime.fromisoformat(key_data['expires_at']) if key_data.get('expires_at') else None,
                permissions=key_data.get('permissions', []),
                metadata=key_data.get('metadata', {})
            )
            api_keys_list.append(api_key)
        
        # Convert limits
        limits_data = self.limits or {}
        limits = ApplicationLimits(
            requests_per_minute=limits_data.get('requests_per_minute', 10),
            requests_per_hour=limits_data.get('requests_per_hour', 100),
            requests_per_day=limits_data.get('requests_per_day', 1000),
            requests_per_month=limits_data.get('requests_per_month', 10000),
            max_file_size_mb=limits_data.get('max_file_size_mb', 10),
            max_concurrent_jobs=limits_data.get('max_concurrent_jobs', 5),
            allowed_file_types=limits_data.get('allowed_file_types', ['image/jpeg', 'image/png', 'application/pdf']),
            priority_processing=limits_data.get('priority_processing', False)
        )
        
        # Convert stats
        stats_data = self.stats or {}
        stats = ApplicationStats(
            total_requests=stats_data.get('total_requests', 0),
            successful_requests=stats_data.get('successful_requests', 0),
            failed_requests=stats_data.get('failed_requests', 0),
            total_processing_time=stats_data.get('total_processing_time', 0.0),
            average_processing_time=stats_data.get('average_processing_time', 0.0),
            total_cost=stats_data.get('total_cost', 0.0),
            current_month_requests=stats_data.get('current_month_requests', 0),
            current_month_cost=stats_data.get('current_month_cost', 0.0),
            last_request_at=datetime.fromisoformat(stats_data['last_request_at']) if stats_data.get('last_request_at') else None
        )
        
        return Application(
            id=self.id,
            user_id=self.user_id,
            name=self.name,
            description=self.description,
            status=self.status,
            tier=self.tier,
            website_url=self.website_url,
            callback_url=self.callback_url,
            contact_email=self.contact_email,
            api_keys=api_keys_list,
            limits=limits,
            stats=stats,
            approved_at=self.approved_at,
            approved_by=self.approved_by,
            approval_notes=self.approval_notes,
            suspended_at=self.suspended_at,
            suspended_by=self.suspended_by,
            suspension_reason=self.suspension_reason,
            last_used_at=self.last_used_at,
            last_api_call_at=self.last_api_call_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            metadata=self.extra_metadata or {}
        )
    
    @classmethod
    def from_domain_entity(cls, application):
        """Create database model from domain entity.
        
        Args:
            application: Application domain entity
            
        Returns:
            ApplicationModel instance
        """
        # Convert API keys to dict list
        api_keys_list = []
        for api_key in application.api_keys:
            key_dict = {
                'key_id': api_key.key_id,
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
        
        # Convert limits to dict
        limits_dict = {
            'requests_per_minute': application.limits.requests_per_minute,
            'requests_per_hour': application.limits.requests_per_hour,
            'requests_per_day': application.limits.requests_per_day,
            'requests_per_month': application.limits.requests_per_month,
            'max_file_size_mb': application.limits.max_file_size_mb,
            'max_concurrent_jobs': application.limits.max_concurrent_jobs,
            'allowed_file_types': application.limits.allowed_file_types,
            'priority_processing': application.limits.priority_processing
        }
        
        # Convert stats to dict
        stats_dict = {
            'total_requests': application.stats.total_requests,
            'successful_requests': application.stats.successful_requests,
            'failed_requests': application.stats.failed_requests,
            'total_processing_time': application.stats.total_processing_time,
            'average_processing_time': application.stats.average_processing_time,
            'total_cost': application.stats.total_cost,
            'current_month_requests': application.stats.current_month_requests,
            'current_month_cost': application.stats.current_month_cost,
            'last_request_at': application.stats.last_request_at.isoformat() if application.stats.last_request_at else None
        }
        
        return cls(
            id=application.id,
            user_id=application.user_id,
            name=application.name,
            description=application.description,
            status=application.status,
            tier=application.tier,
            website_url=application.website_url,
            callback_url=application.callback_url,
            contact_email=application.contact_email,
            api_keys=api_keys_list,
            limits=limits_dict,
            stats=stats_dict,
            approved_at=application.approved_at,
            approved_by=application.approved_by,
            approval_notes=application.approval_notes,
            suspended_at=application.suspended_at,
            suspended_by=application.suspended_by,
            suspension_reason=application.suspension_reason,
            last_used_at=application.last_used_at,
            last_api_call_at=application.last_api_call_at,
            created_at=application.created_at,
            updated_at=application.updated_at,
            deleted_at=application.deleted_at,
            extra_metadata=application.metadata
        )
    
    def update_from_domain_entity(self, application) -> None:
        """Update database model from domain entity.
        
        Args:
            application: Application domain entity
        """
        # Update basic fields
        self.name = application.name
        self.description = application.description
        self.status = application.status
        self.tier = application.tier
        self.website_url = application.website_url
        self.callback_url = application.callback_url
        self.contact_email = application.contact_email
        self.approved_at = application.approved_at
        self.approved_by = application.approved_by
        self.approval_notes = application.approval_notes
        self.suspended_at = application.suspended_at
        self.suspended_by = application.suspended_by
        self.suspension_reason = application.suspension_reason
        self.last_used_at = application.last_used_at
        self.last_api_call_at = application.last_api_call_at
        self.deleted_at = application.deleted_at
        self.extra_metadata = application.metadata
        
        # Update API keys
        api_keys_list = []
        for api_key in application.api_keys:
            key_dict = {
                'key_id': api_key.key_id,
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
        self.api_keys = api_keys_list
        
        # Update limits
        self.limits = {
            'requests_per_minute': application.limits.requests_per_minute,
            'requests_per_hour': application.limits.requests_per_hour,
            'requests_per_day': application.limits.requests_per_day,
            'requests_per_month': application.limits.requests_per_month,
            'max_file_size_mb': application.limits.max_file_size_mb,
            'max_concurrent_jobs': application.limits.max_concurrent_jobs,
            'allowed_file_types': application.limits.allowed_file_types,
            'priority_processing': application.limits.priority_processing
        }
        
        # Update stats
        self.stats = {
            'total_requests': application.stats.total_requests,
            'successful_requests': application.stats.successful_requests,
            'failed_requests': application.stats.failed_requests,
            'total_processing_time': application.stats.total_processing_time,
            'average_processing_time': application.stats.average_processing_time,
            'total_cost': application.stats.total_cost,
            'current_month_requests': application.stats.current_month_requests,
            'current_month_cost': application.stats.current_month_cost,
            'last_request_at': application.stats.last_request_at.isoformat() if application.stats.last_request_at else None
        }
        
        # Update timestamps
        self.updated_at = application.updated_at or datetime.utcnow()
    
    @property
    def is_active(self) -> bool:
        """Check if application is active.
        
        Returns:
            True if application is active
        """
        return (
            self.status == ApplicationStatus.APPROVED and
            self.suspended_at is None and
            self.deleted_at is None
        )
    
    @property
    def active_api_keys_count(self) -> int:
        """Get count of active API keys.
        
        Returns:
            Number of active API keys
        """
        if not self.api_keys:
            return 0
        
        return sum(
            1 for key in self.api_keys
            if key.get('status') == APIKeyStatus.ACTIVE.value
        )
    
    @property
    def current_month_usage_percentage(self) -> float:
        """Get current month usage as percentage of limit.
        
        Returns:
            Usage percentage (0-100)
        """
        if not self.stats or not self.limits:
            return 0.0
        
        current_requests = self.stats.get('current_month_requests', 0)
        monthly_limit = self.limits.get('requests_per_month', 1)
        
        return min((current_requests / monthly_limit) * 100, 100.0)
    
    @property
    def success_rate(self) -> float:
        """Get success rate percentage.
        
        Returns:
            Success rate percentage (0-100)
        """
        if not self.stats:
            return 0.0
        
        total = self.stats.get('total_requests', 0)
        successful = self.stats.get('successful_requests', 0)
        
        if total == 0:
            return 0.0
        
        return (successful / total) * 100
    
    def get_api_key_by_id(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get API key by ID.
        
        Args:
            key_id: API key ID
            
        Returns:
            API key data or None
        """
        if not self.api_keys:
            return None
        
        for key in self.api_keys:
            if key.get('key_id') == key_id:
                return key
        
        return None
    
    def __repr__(self) -> str:
        """String representation of the application model."""
        return f"<ApplicationModel(id={self.id}, name='{self.name}', status={self.status})>"