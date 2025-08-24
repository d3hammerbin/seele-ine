#!/usr/bin/env python3
"""
User Database Model

SQLAlchemy model for user data persistence.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship

from ..base import BaseModel
from ....domain.entities.user import UserRole, UserStatus, SubscriptionPlan


class UserModel(BaseModel):
    """User database model."""
    
    __tablename__ = "users"
    
    # Basic information
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    password_hash = Column(
        String(255),
        nullable=False
    )
    
    # Personal information
    first_name = Column(
        String(100),
        nullable=False
    )
    
    last_name = Column(
        String(100),
        nullable=False
    )
    
    phone = Column(
        String(20),
        nullable=True
    )
    
    # User status and role
    role = Column(
        SQLEnum(UserRole),
        nullable=False,
        default=UserRole.USER,
        index=True
    )
    
    status = Column(
        SQLEnum(UserStatus),
        nullable=False,
        default=UserStatus.ACTIVE,
        index=True
    )
    
    # Subscription information
    subscription_plan = Column(
        SQLEnum(SubscriptionPlan),
        nullable=False,
        default=SubscriptionPlan.FREE,
        index=True
    )
    
    subscription_start_date = Column(
        DateTime,
        nullable=True
    )
    
    subscription_end_date = Column(
        DateTime,
        nullable=True
    )
    
    # Authentication and security
    email_verified = Column(
        Boolean,
        nullable=False,
        default=False
    )
    
    email_verification_token = Column(
        String(255),
        nullable=True
    )
    
    password_reset_token = Column(
        String(255),
        nullable=True
    )
    
    password_reset_expires = Column(
        DateTime,
        nullable=True
    )
    
    two_factor_enabled = Column(
        Boolean,
        nullable=False,
        default=False
    )
    
    two_factor_secret = Column(
        String(255),
        nullable=True
    )
    
    # Activity tracking
    last_login_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    last_logout_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    last_login_ip = Column(
        String(45),  # IPv6 compatible
        nullable=True
    )
    
    login_count = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    # User preferences (stored as JSON)
    preferences = Column(
        JSON,
        nullable=False,
        default=dict
    )
    
    # User statistics (stored as JSON)
    statistics = Column(
        JSON,
        nullable=False,
        default=dict
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
    applications = relationship(
        "ApplicationModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    credentials = relationship(
        "CredentialModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    processing_jobs = relationship(
        "ProcessingJobModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    billing_records = relationship(
        "BillingModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def to_domain_entity(self):
        """Convert database model to domain entity.
        
        Returns:
            User domain entity
        """
        from ....domain.entities.user import User, UserPreferences, UserStats
        
        # Convert preferences
        prefs_data = self.preferences or {}
        preferences = UserPreferences(
            language=prefs_data.get('language', 'es'),
            timezone=prefs_data.get('timezone', 'America/Mexico_City'),
            email_notifications=prefs_data.get('email_notifications', True),
            sms_notifications=prefs_data.get('sms_notifications', False),
            theme=prefs_data.get('theme', 'light')
        )
        
        # Convert statistics
        stats_data = self.statistics or {}
        statistics = UserStats(
            total_credentials_processed=stats_data.get('total_credentials_processed', 0),
            successful_extractions=stats_data.get('successful_extractions', 0),
            failed_extractions=stats_data.get('failed_extractions', 0),
            total_api_calls=stats_data.get('total_api_calls', 0),
            total_cost_usd=stats_data.get('total_cost_incurred', 0.0),
            last_activity=None,
            credits_used=stats_data.get('credits_used', 0),
            credits_remaining=stats_data.get('credits_remaining', 0)
        )
        
        return User(
            id=self.id,
            email=self.email,
            username=self.username,
            password_hash=self.password_hash,
            first_name=self.first_name,
            last_name=self.last_name,
            phone=self.phone,
            role=self.role,
            status=self.status,
            subscription_plan=self.subscription_plan,
            is_email_verified=self.email_verified,
            email_verification_token=self.email_verification_token,
            password_reset_token=self.password_reset_token,
            password_reset_expires=self.password_reset_expires,
            preferences=preferences,
            stats=statistics,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_login=self.last_login_at,
            last_logout=self.last_logout_at,
            metadata=self.extra_metadata or {}
        )
    
    @classmethod
    def from_domain_entity(cls, user):
        """Create database model from domain entity.
        
        Args:
            user: User domain entity
            
        Returns:
            UserModel instance
        """
        # Convert preferences to dict
        preferences_dict = {
            'language': user.preferences.language,
            'timezone': user.preferences.timezone,
            'email_notifications': user.preferences.email_notifications,
            'sms_notifications': user.preferences.sms_notifications,
            'theme': user.preferences.theme
        }
        
        # Convert statistics to dict
        statistics_dict = {
            'total_credentials_processed': user.stats.total_credentials_processed,
            'successful_extractions': user.stats.successful_extractions,
            'failed_extractions': user.stats.failed_extractions,
            'total_api_calls': user.stats.total_api_calls,
            'total_cost_incurred': user.stats.total_cost_usd,
            'credits_used': user.stats.credits_used,
            'credits_remaining': user.stats.credits_remaining
        }
        
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            password_hash=user.password_hash,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            role=user.role,
            status=user.status,
            subscription_plan=user.subscription_plan,
            email_verified=user.is_email_verified,
            email_verification_token=user.email_verification_token,
            password_reset_token=user.password_reset_token,
            password_reset_expires=user.password_reset_expires,
            last_login_at=user.last_login,
            preferences=preferences_dict,
            statistics=statistics_dict,
            created_at=user.created_at,
            updated_at=user.updated_at,
            extra_metadata=user.metadata
        )
    
    def update_from_domain_entity(self, user) -> None:
        """Update database model from domain entity.
        
        Args:
            user: User domain entity
        """
        # Update basic fields
        self.email = user.email
        self.username = user.username
        self.password_hash = user.password_hash
        self.first_name = user.first_name
        self.last_name = user.last_name
        self.phone = user.phone
        self.role = user.role
        self.status = user.status
        self.subscription_plan = user.subscription_plan
        self.email_verified = user.is_email_verified
        self.email_verification_token = user.email_verification_token
        self.password_reset_token = user.password_reset_token
        self.password_reset_expires = user.password_reset_expires
        self.last_login_at = user.last_login
        self.last_logout_at = user.last_logout
        self.extra_metadata = user.metadata
        
        # Update preferences
        self.preferences = {
            'language': user.preferences.language,
            'timezone': user.preferences.timezone,
            'email_notifications': user.preferences.email_notifications,
            'sms_notifications': user.preferences.sms_notifications,
            'theme': user.preferences.theme
        }
        
        # Update statistics
        self.statistics = {
            'total_credentials_processed': user.stats.total_credentials_processed,
            'successful_extractions': user.stats.successful_extractions,
            'failed_extractions': user.stats.failed_extractions,
            'total_api_calls': user.stats.total_api_calls,
            'total_cost_incurred': user.stats.total_cost_usd,
            'credits_used': user.stats.credits_used,
            'credits_remaining': user.stats.credits_remaining
        }
        
        # Update timestamps
        self.updated_at = user.updated_at or datetime.utcnow()
    
    @property
    def is_active(self) -> bool:
        """Check if user is active.
        
        Returns:
            True if user is active
        """
        return (
            self.status == UserStatus.ACTIVE and
            self.deleted_at is None
        )
    
    @property
    def full_name(self) -> str:
        """Get user's full name.
        
        Returns:
            Full name
        """
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def has_active_subscription(self) -> bool:
        """Check if user has active subscription.
        
        Returns:
            True if subscription is active
        """
        if self.subscription_plan == SubscriptionPlan.FREE:
            return True
        
        if not self.subscription_end_date:
            return False
        
        return datetime.utcnow() <= self.subscription_end_date
    
    def __repr__(self) -> str:
        """String representation of the user model."""
        return f"<UserModel(id={self.id}, email='{self.email}', username='{self.username}')>"