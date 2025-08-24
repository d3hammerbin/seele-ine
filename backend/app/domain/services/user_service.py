#!/usr/bin/env python3
"""
User Domain Service

Contains business logic for user operations that don't belong to a single entity.
Handles complex user-related business rules and validations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import re

from ..entities.user import User, UserRole, UserStatus, SubscriptionPlan
from ..repositories.user_repository import UserRepository
from ...core.exceptions.base import (
    ValidationException, BusinessLogicError, NotFoundError
)


class UserService:
    """Domain service for user business logic."""

    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def create_user(
        self,
        email: str,
        username: str,
        password_hash: str,
        full_name: str,
        role: UserRole = UserRole.USER,
        subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    ) -> User:
        """Create a new user with business validations.
        
        Args:
            email: User's email address
            username: User's username
            password_hash: Hashed password
            full_name: User's full name
            role: User role (default: USER)
            subscription_plan: Subscription plan (default: FREE)
            
        Returns:
            The created user
            
        Raises:
            ValidationException: If validation fails
            BusinessLogicError: If business rules are violated
        """
        # Validate email format
        if not self._is_valid_email(email):
            raise ValidationException("Invalid email format")
        
        # Validate username format
        if not self._is_valid_username(username):
            raise ValidationException(
                "Username must be 3-30 characters, alphanumeric and underscores only"
            )
        
        # Check if email already exists
        existing_user = await self._user_repository.get_by_email(email)
        if existing_user:
            raise BusinessLogicError("Email already registered")
        
        # Check if username already exists
        existing_user = await self._user_repository.get_by_username(username)
        if existing_user:
            raise BusinessLogicError("Username already taken")
        
        # Create user entity
        user = User.create(
            email=email,
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            subscription_plan=subscription_plan
        )
        
        # Save to repository
        return await self._user_repository.create(user)

    async def authenticate_user(self, email: str, password_hash: str) -> Optional[User]:
        """Authenticate a user by email and password.
        
        Args:
            email: User's email address
            password_hash: Hashed password to verify
            
        Returns:
            The authenticated user if successful, None otherwise
            
        Raises:
            ValidationException: If input validation fails
        """
        if not email or not password_hash:
            raise ValidationException("Email and password are required")
        
        user = await self._user_repository.get_by_email(email)
        if not user:
            return None
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            return None
        
        # Verify password (this would typically use a password hashing library)
        if user.password_hash != password_hash:
            return None
        
        # Update last login
        await self._user_repository.update_last_login(user.id)
        
        return user

    async def update_user_profile(
        self,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> User:
        """Update user profile with business validations.
        
        Args:
            user_id: User's unique identifier
            updates: Dictionary of fields to update
            
        Returns:
            The updated user
            
        Raises:
            NotFoundError: If user not found
            ValidationException: If validation fails
            BusinessLogicError: If business rules are violated
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Validate email if being updated
        if 'email' in updates:
            new_email = updates['email']
            if not self._is_valid_email(new_email):
                raise ValidationException("Invalid email format")
            
            # Check if new email is already taken by another user
            existing_user = await self._user_repository.get_by_email(new_email)
            if existing_user and existing_user.id != user_id:
                raise BusinessLogicError("Email already registered")
        
        # Validate username if being updated
        if 'username' in updates:
            new_username = updates['username']
            if not self._is_valid_username(new_username):
                raise ValidationException(
                    "Username must be 3-30 characters, alphanumeric and underscores only"
                )
            
            # Check if new username is already taken by another user
            existing_user = await self._user_repository.get_by_username(new_username)
            if existing_user and existing_user.id != user_id:
                raise BusinessLogicError("Username already taken")
        
        # Apply updates to user entity
        for field, value in updates.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        return await self._user_repository.update(user)

    async def change_user_password(
        self,
        user_id: UUID,
        current_password_hash: str,
        new_password_hash: str
    ) -> bool:
        """Change user password with current password verification.
        
        Args:
            user_id: User's unique identifier
            current_password_hash: Current password hash for verification
            new_password_hash: New password hash
            
        Returns:
            True if password was changed successfully
            
        Raises:
            NotFoundError: If user not found
            ValidationException: If current password is incorrect
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Verify current password
        if user.password_hash != current_password_hash:
            raise ValidationException("Current password is incorrect")
        
        # Update password
        user.password_hash = new_password_hash
        user.updated_at = datetime.utcnow()
        
        await self._user_repository.update(user)
        return True

    async def upgrade_subscription(
        self,
        user_id: UUID,
        new_plan: SubscriptionPlan
    ) -> User:
        """Upgrade user subscription plan.
        
        Args:
            user_id: User's unique identifier
            new_plan: New subscription plan
            
        Returns:
            The updated user
            
        Raises:
            NotFoundError: If user not found
            BusinessLogicError: If upgrade is not valid
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Validate upgrade path
        if not self._is_valid_upgrade(user.subscription_plan, new_plan):
            raise BusinessLogicError(f"Cannot upgrade from {user.subscription_plan} to {new_plan}")
        
        # Update subscription
        user.subscription_plan = new_plan
        user.updated_at = datetime.utcnow()
        
        return await self._user_repository.update(user)

    async def suspend_user(self, user_id: UUID, reason: str) -> User:
        """Suspend a user account.
        
        Args:
            user_id: User's unique identifier
            reason: Reason for suspension
            
        Returns:
            The suspended user
            
        Raises:
            NotFoundError: If user not found
            BusinessLogicError: If user cannot be suspended
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        if user.status == UserStatus.SUSPENDED:
            raise BusinessLogicError("User is already suspended")
        
        if user.role == UserRole.ADMIN:
            raise BusinessLogicError("Cannot suspend admin users")
        
        user.status = UserStatus.SUSPENDED
        user.updated_at = datetime.utcnow()
        
        return await self._user_repository.update(user)

    async def reactivate_user(self, user_id: UUID) -> User:
        """Reactivate a suspended user account.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            The reactivated user
            
        Raises:
            NotFoundError: If user not found
            BusinessLogicError: If user cannot be reactivated
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        if user.status != UserStatus.SUSPENDED:
            raise BusinessLogicError("User is not suspended")
        
        user.status = UserStatus.ACTIVE
        user.updated_at = datetime.utcnow()
        
        return await self._user_repository.update(user)

    async def get_user_statistics(self, user_id: UUID) -> Dict[str, Any]:
        """Get comprehensive user statistics.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dictionary containing user statistics
            
        Raises:
            NotFoundError: If user not found
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        stats = await self._user_repository.get_user_stats(user_id)
        
        return {
            'user_id': user_id,
            'account_age_days': (datetime.utcnow() - user.created_at).days,
            'subscription_plan': user.subscription_plan.value,
            'status': user.status.value,
            'last_login': user.last_login,
            'statistics': stats
        }

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email format is valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _is_valid_username(self, username: str) -> bool:
        """Validate username format.
        
        Args:
            username: Username to validate
            
        Returns:
            True if username format is valid
        """
        if not username or len(username) < 3 or len(username) > 30:
            return False
        
        pattern = r'^[a-zA-Z0-9_]+$'
        return bool(re.match(pattern, username))

    def _is_valid_upgrade(self, current_plan: SubscriptionPlan, new_plan: SubscriptionPlan) -> bool:
        """Validate subscription upgrade path.
        
        Args:
            current_plan: Current subscription plan
            new_plan: Proposed new subscription plan
            
        Returns:
            True if upgrade is valid
        """
        # Define upgrade hierarchy
        hierarchy = {
            SubscriptionPlan.FREE: 0,
            SubscriptionPlan.BASIC: 1,
            SubscriptionPlan.PREMIUM: 2,
            SubscriptionPlan.ENTERPRISE: 3
        }
        
        return hierarchy[new_plan] > hierarchy[current_plan]