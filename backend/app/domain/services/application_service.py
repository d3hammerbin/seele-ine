#!/usr/bin/env python3
"""
Application Domain Service

Contains business logic for application operations.
Handles complex application-related business rules and validations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import secrets
import string

from ..entities.application import (
    Application, ApplicationStatus, ApplicationTier, APIKeyStatus
)
from ..entities.user import User, SubscriptionPlan
from ..repositories.application_repository import ApplicationRepository
from ..repositories.user_repository import UserRepository
from ...core.exceptions.base import (
    ValidationException, BusinessLogicError, NotFoundError, AuthorizationException
)


class ApplicationService:
    """Domain service for application business logic."""

    # API key configuration
    API_KEY_LENGTH = 32
    API_KEY_PREFIX = "sk-seele-"
    
    # Application limits by tier
    TIER_LIMITS = {
        ApplicationTier.BASIC: {
            'daily_requests': 100,
            'monthly_requests': 2000,
            'rate_limit_per_minute': 10,
            'max_file_size_mb': 5,
            'concurrent_requests': 2
        },
        ApplicationTier.PREMIUM: {
            'daily_requests': 1000,
            'monthly_requests': 25000,
            'rate_limit_per_minute': 50,
            'max_file_size_mb': 10,
            'concurrent_requests': 5
        },
        ApplicationTier.ENTERPRISE: {
            'daily_requests': 10000,
            'monthly_requests': 250000,
            'rate_limit_per_minute': 200,
            'max_file_size_mb': 20,
            'concurrent_requests': 20
        }
    }

    def __init__(
        self,
        application_repository: ApplicationRepository,
        user_repository: UserRepository
    ):
        self._application_repository = application_repository
        self._user_repository = user_repository

    async def create_application(
        self,
        user_id: UUID,
        name: str,
        description: str,
        tier: ApplicationTier = ApplicationTier.BASIC
    ) -> Application:
        """Create a new application.
        
        Args:
            user_id: User's unique identifier
            name: Application name
            description: Application description
            tier: Application tier
            
        Returns:
            The created application
            
        Raises:
            ValidationException: If validation fails
            BusinessLogicError: If business rules are violated
            NotFoundError: If user not found
        """
        # Validate user exists and is active
        user = await self._user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise NotFoundError("User not found or inactive")
        
        # Validate application name
        if not name or len(name.strip()) < 3:
            raise ValidationException("Application name must be at least 3 characters")
        
        if len(name) > 100:
            raise ValidationException("Application name must be less than 100 characters")
        
        # Check if application name already exists for this user
        existing_app = await self._application_repository.get_by_name(name.strip(), user_id)
        if existing_app:
            raise BusinessLogicError("Application name already exists")
        
        # Check user's application limits
        await self._check_application_creation_limits(user, tier)
        
        # Get tier limits
        limits = self.TIER_LIMITS[tier]
        
        # Create application
        application = Application.create(
            user_id=user_id,
            name=name.strip(),
            description=description.strip() if description else "",
            tier=tier,
            daily_requests=limits['daily_requests'],
            monthly_requests=limits['monthly_requests'],
            rate_limit_per_minute=limits['rate_limit_per_minute'],
            max_file_size_mb=limits['max_file_size_mb'],
            concurrent_requests=limits['concurrent_requests']
        )
        
        # Generate initial API key
        api_key = self._generate_api_key()
        application.create_api_key(api_key)
        
        return await self._application_repository.create(application)

    async def update_application(
        self,
        application_id: UUID,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> Application:
        """Update an application.
        
        Args:
            application_id: Application's unique identifier
            user_id: User's unique identifier
            updates: Dictionary of fields to update
            
        Returns:
            The updated application
            
        Raises:
            NotFoundError: If application not found
            AuthorizationException: If user doesn't own the application
            ValidationException: If validation fails
            BusinessLogicError: If business rules are violated
        """
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        if application.user_id != user_id:
            raise AuthorizationException("User does not own this application")
        
        # Validate name if being updated
        if 'name' in updates:
            new_name = updates['name'].strip()
            if len(new_name) < 3:
                raise ValidationException("Application name must be at least 3 characters")
            
            if len(new_name) > 100:
                raise ValidationException("Application name must be less than 100 characters")
            
            # Check if new name already exists for this user
            existing_app = await self._application_repository.get_by_name(new_name, user_id)
            if existing_app and existing_app.id != application_id:
                raise BusinessLogicError("Application name already exists")
        
        # Apply updates
        for field, value in updates.items():
            if field in ['name', 'description'] and hasattr(application, field):
                setattr(application, field, value.strip() if isinstance(value, str) else value)
        
        application.updated_at = datetime.utcnow()
        
        return await self._application_repository.update(application)

    async def upgrade_application_tier(
        self,
        application_id: UUID,
        user_id: UUID,
        new_tier: ApplicationTier
    ) -> Application:
        """Upgrade application tier.
        
        Args:
            application_id: Application's unique identifier
            user_id: User's unique identifier
            new_tier: New application tier
            
        Returns:
            The upgraded application
            
        Raises:
            NotFoundError: If application not found
            AuthorizationException: If user doesn't own the application
            BusinessLogicError: If upgrade is not valid
        """
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        if application.user_id != user_id:
            raise AuthorizationException("User does not own this application")
        
        # Validate upgrade path
        if not self._is_valid_tier_upgrade(application.tier, new_tier):
            raise BusinessLogicError(f"Cannot upgrade from {application.tier} to {new_tier}")
        
        # Check user's subscription allows this tier
        user = await self._user_repository.get_by_id(user_id)
        if not self._user_can_access_tier(user.subscription_plan, new_tier):
            raise BusinessLogicError(
                f"User's subscription plan ({user.subscription_plan}) does not allow {new_tier} tier"
            )
        
        # Update application with new tier limits
        limits = self.TIER_LIMITS[new_tier]
        application.upgrade_tier(
            new_tier=new_tier,
            daily_requests=limits['daily_requests'],
            monthly_requests=limits['monthly_requests'],
            rate_limit_per_minute=limits['rate_limit_per_minute'],
            max_file_size_mb=limits['max_file_size_mb'],
            concurrent_requests=limits['concurrent_requests']
        )
        
        return await self._application_repository.update(application)

    async def generate_new_api_key(
        self,
        application_id: UUID,
        user_id: UUID,
        name: Optional[str] = None
    ) -> str:
        """Generate a new API key for an application.
        
        Args:
            application_id: Application's unique identifier
            user_id: User's unique identifier
            name: Optional name for the API key
            
        Returns:
            The new API key
            
        Raises:
            NotFoundError: If application not found
            AuthorizationException: If user doesn't own the application
            BusinessLogicError: If API key limit exceeded
        """
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        if application.user_id != user_id:
            raise AuthorizationException("User does not own this application")
        
        # Check API key limit
        active_keys = [key for key in application.api_keys if key.status == APIKeyStatus.ACTIVE]
        if len(active_keys) >= 5:  # Maximum 5 active keys per application
            raise BusinessLogicError("Maximum number of API keys reached (5)")
        
        # Generate new API key
        api_key = self._generate_api_key()
        application.create_api_key(api_key, name)
        
        await self._application_repository.update(application)
        
        return api_key

    async def revoke_api_key(
        self,
        application_id: UUID,
        user_id: UUID,
        api_key: str
    ) -> bool:
        """Revoke an API key.
        
        Args:
            application_id: Application's unique identifier
            user_id: User's unique identifier
            api_key: API key to revoke
            
        Returns:
            True if revocation was successful
            
        Raises:
            NotFoundError: If application not found
            AuthorizationException: If user doesn't own the application
            BusinessLogicError: If API key not found or already revoked
        """
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        if application.user_id != user_id:
            raise AuthorizationException("User does not own this application")
        
        # Find and revoke the API key
        success = application.revoke_api_key(api_key)
        if not success:
            raise BusinessLogicError("API key not found or already revoked")
        
        await self._application_repository.update(application)
        
        return True

    async def suspend_application(
        self,
        application_id: UUID,
        reason: str,
        admin_user_id: Optional[UUID] = None
    ) -> Application:
        """Suspend an application.
        
        Args:
            application_id: Application's unique identifier
            reason: Reason for suspension
            admin_user_id: Optional admin user ID for audit
            
        Returns:
            The suspended application
            
        Raises:
            NotFoundError: If application not found
            BusinessLogicError: If application cannot be suspended
        """
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        if application.status == ApplicationStatus.SUSPENDED:
            raise BusinessLogicError("Application is already suspended")
        
        application.suspend(reason)
        
        return await self._application_repository.update(application)

    async def reactivate_application(
        self,
        application_id: UUID,
        admin_user_id: Optional[UUID] = None
    ) -> Application:
        """Reactivate a suspended application.
        
        Args:
            application_id: Application's unique identifier
            admin_user_id: Optional admin user ID for audit
            
        Returns:
            The reactivated application
            
        Raises:
            NotFoundError: If application not found
            BusinessLogicError: If application cannot be reactivated
        """
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        if application.status != ApplicationStatus.SUSPENDED:
            raise BusinessLogicError("Application is not suspended")
        
        # Check if user is still active
        user = await self._user_repository.get_by_id(application.user_id)
        if not user or not user.is_active:
            raise BusinessLogicError("Cannot reactivate application for inactive user")
        
        application.reactivate()
        
        return await self._application_repository.update(application)

    async def update_usage_statistics(
        self,
        application_id: UUID,
        requests_count: int = 0,
        tokens_used: int = 0,
        cost_incurred: float = 0.0
    ) -> bool:
        """Update application usage statistics.
        
        Args:
            application_id: Application's unique identifier
            requests_count: Number of requests to add
            tokens_used: Number of tokens to add
            cost_incurred: Cost to add
            
        Returns:
            True if update was successful
            
        Raises:
            NotFoundError: If application not found
        """
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        application.increment_usage(requests_count, tokens_used, cost_incurred)
        
        await self._application_repository.update(application)
        
        return True

    async def get_application_analytics(
        self,
        application_id: UUID,
        user_id: UUID,
        date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """Get application analytics.
        
        Args:
            application_id: Application's unique identifier
            user_id: User's unique identifier
            date_range: Optional date range tuple (start, end)
            
        Returns:
            Dictionary containing application analytics
            
        Raises:
            NotFoundError: If application not found
            AuthorizationException: If user doesn't own the application
        """
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        if application.user_id != user_id:
            raise AuthorizationException("User does not own this application")
        
        # Get usage statistics from repository
        usage_stats = await self._application_repository.get_usage_stats(application_id)
        
        return {
            'application_id': application_id,
            'name': application.name,
            'tier': application.tier.value,
            'status': application.status.value,
            'created_at': application.created_at,
            'usage_statistics': usage_stats,
            'limits': {
                'daily_requests': application.limits.daily_requests,
                'monthly_requests': application.limits.monthly_requests,
                'rate_limit_per_minute': application.limits.rate_limit_per_minute
            },
            'api_keys_count': len([k for k in application.api_keys if k.status == APIKeyStatus.ACTIVE])
        }

    async def _check_application_creation_limits(
        self,
        user: User,
        tier: ApplicationTier
    ) -> None:
        """Check if user can create an application with the specified tier.
        
        Args:
            user: User entity
            tier: Requested application tier
            
        Raises:
            BusinessLogicError: If limits are exceeded
        """
        # Check subscription plan allows this tier
        if not self._user_can_access_tier(user.subscription_plan, tier):
            raise BusinessLogicError(
                f"User's subscription plan ({user.subscription_plan}) does not allow {tier} tier"
            )
        
        # Check maximum applications per user
        user_apps = await self._application_repository.get_by_user_id(user.id)
        active_apps = [app for app in user_apps if app.status == ApplicationStatus.ACTIVE]
        
        max_apps_by_plan = {
            SubscriptionPlan.FREE: 1,
            SubscriptionPlan.BASIC: 3,
            SubscriptionPlan.PREMIUM: 10,
            SubscriptionPlan.ENTERPRISE: 50
        }
        
        max_apps = max_apps_by_plan.get(user.subscription_plan, 1)
        if len(active_apps) >= max_apps:
            raise BusinessLogicError(
                f"Maximum number of applications reached ({max_apps} for {user.subscription_plan} plan)"
            )

    def _generate_api_key(self) -> str:
        """Generate a secure API key.
        
        Returns:
            Generated API key
        """
        # Generate random string
        alphabet = string.ascii_letters + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(self.API_KEY_LENGTH))
        
        return f"{self.API_KEY_PREFIX}{random_part}"

    def _is_valid_tier_upgrade(self, current_tier: ApplicationTier, new_tier: ApplicationTier) -> bool:
        """Check if tier upgrade is valid.
        
        Args:
            current_tier: Current application tier
            new_tier: Proposed new tier
            
        Returns:
            True if upgrade is valid
        """
        hierarchy = {
            ApplicationTier.BASIC: 0,
            ApplicationTier.PREMIUM: 1,
            ApplicationTier.ENTERPRISE: 2
        }
        
        return hierarchy[new_tier] > hierarchy[current_tier]

    def _user_can_access_tier(self, subscription_plan: SubscriptionPlan, tier: ApplicationTier) -> bool:
        """Check if user's subscription allows access to application tier.
        
        Args:
            subscription_plan: User's subscription plan
            tier: Application tier
            
        Returns:
            True if access is allowed
        """
        tier_access = {
            SubscriptionPlan.FREE: [ApplicationTier.BASIC],
            SubscriptionPlan.BASIC: [ApplicationTier.BASIC, ApplicationTier.PREMIUM],
            SubscriptionPlan.PREMIUM: [ApplicationTier.BASIC, ApplicationTier.PREMIUM, ApplicationTier.ENTERPRISE],
            SubscriptionPlan.ENTERPRISE: [ApplicationTier.BASIC, ApplicationTier.PREMIUM, ApplicationTier.ENTERPRISE]
        }
        
        return tier in tier_access.get(subscription_plan, [])