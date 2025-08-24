#!/usr/bin/env python3
"""
User Repository Implementation

SQLAlchemy implementation of the UserRepository interface.
Handles database operations for user entities.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.repositories.user_repository import UserRepository
from ...domain.entities.user import User, UserRole, UserStatus, SubscriptionPlan
from ...core.exceptions.base import RepositoryError, NotFoundError
from ..database.models.user import UserModel


class UserRepositoryImpl(UserRepository):
    """
    SQLAlchemy implementation of UserRepository.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, user: User) -> User:
        """Create a new user in the database."""
        try:
            # Convert domain entity to database model
            user_model = UserModel.from_domain_entity(user)
            
            # Add to session and commit
            self._session.add(user_model)
            await self._session.commit()
            await self._session.refresh(user_model)
            
            # Convert back to domain entity
            return user_model.to_domain_entity()
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to create user: {str(e)}")
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        try:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await self._session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            return user_model.to_domain_entity() if user_model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to get user by ID: {str(e)}")
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            stmt = select(UserModel).where(UserModel.email == email.lower())
            result = await self._session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            return user_model.to_domain_entity() if user_model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to get user by email: {str(e)}")
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            stmt = select(UserModel).where(UserModel.username == username.lower())
            result = await self._session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            return user_model.to_domain_entity() if user_model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to get user by username: {str(e)}")
    
    async def update(self, user: User) -> User:
        """Update an existing user."""
        try:
            # Get existing user model
            stmt = select(UserModel).where(UserModel.id == user.id)
            result = await self._session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                raise NotFoundError(f"User with ID {user.id} not found")
            
            # Update fields from domain entity
            user_model.email = user.email.lower()
            user_model.username = user.username.lower() if user.username else None
            user_model.password_hash = user.password_hash
            user_model.phone = user.phone
            user_model.role = user.role
            user_model.status = user.status
            user_model.subscription_plan = user.subscription_plan
            user_model.email_verified = user.is_email_verified
            user_model.last_login_at = user.last_login
            user_model.updated_at = datetime.utcnow()
            user_model.extra_metadata = user.metadata
            
            await self._session.commit()
            await self._session.refresh(user_model)
            
            return user_model.to_domain_entity()
            
        except NotFoundError:
            raise
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to update user: {str(e)}")
    
    async def delete(self, user_id: UUID) -> bool:
        """Soft delete a user."""
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    status=UserStatus.DELETED,
                    deleted_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to delete user: {str(e)}")
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        subscription_plan: Optional[SubscriptionPlan] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> List[User]:
        """List users with optional filters."""
        try:
            stmt = select(UserModel)
            
            # Apply filters
            if status:
                stmt = stmt.where(UserModel.status == status)
            if role:
                stmt = stmt.where(UserModel.role == role)
            if subscription_plan:
                stmt = stmt.where(UserModel.subscription_plan == subscription_plan)
            
            # Apply search filter
            if search:
                search_filter = or_(
                    UserModel.username.ilike(f"%{search}%"),
                    UserModel.email.ilike(f"%{search}%"),
                    UserModel.first_name.ilike(f"%{search}%"),
                    UserModel.last_name.ilike(f"%{search}%")
                )
                stmt = stmt.where(search_filter)
            
            # Apply sorting
            if hasattr(UserModel, sort_by):
                sort_column = getattr(UserModel, sort_by)
                if sort_desc:
                    stmt = stmt.order_by(sort_column.desc())
                else:
                    stmt = stmt.order_by(sort_column.asc())
            else:
                stmt = stmt.order_by(UserModel.created_at.desc())
            
            # Apply pagination
            stmt = stmt.offset(skip).limit(limit)
            
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            return [user_model.to_domain_entity() for user_model in user_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to list users: {str(e)}")
    
    async def count_users(
        self,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        subscription_plan: Optional[SubscriptionPlan] = None,
        search: Optional[str] = None
    ) -> int:
        """Count users with optional filters."""
        try:
            stmt = select(func.count(UserModel.id))
            
            # Apply filters
            if status:
                stmt = stmt.where(UserModel.status == status)
            if role:
                stmt = stmt.where(UserModel.role == role)
            if subscription_plan:
                stmt = stmt.where(UserModel.subscription_plan == subscription_plan)
            
            # Apply search filter
            if search:
                search_filter = or_(
                    UserModel.username.ilike(f"%{search}%"),
                    UserModel.email.ilike(f"%{search}%"),
                    UserModel.first_name.ilike(f"%{search}%"),
                    UserModel.last_name.ilike(f"%{search}%")
                )
                stmt = stmt.where(search_filter)
            
            result = await self._session.execute(stmt)
            return result.scalar()
            
        except Exception as e:
            raise RepositoryError(f"Failed to count users: {str(e)}")
    
    async def search_users(
        self,
        query: str,
        limit: int = 50
    ) -> List[User]:
        """Search users by email, username, or full name."""
        try:
            search_term = f"%{query.lower()}%"
            
            stmt = select(UserModel).where(
                or_(
                    UserModel.email.ilike(search_term),
                    UserModel.username.ilike(search_term),
                    UserModel.full_name.ilike(search_term)
                )
            )
            
            stmt = stmt.limit(limit)
            stmt = stmt.order_by(UserModel.created_at.desc())
            
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            return [user_model.to_domain_entity() for user_model in user_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to search users: {str(e)}")
    
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get all users with a specific role."""
        try:
            stmt = select(UserModel).where(UserModel.role == role)
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            return [user_model.to_domain_entity() for user_model in user_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get users by role: {str(e)}")
    
    async def get_users_by_subscription_plan(self, plan: SubscriptionPlan) -> List[User]:
        """Get all users with a specific subscription plan."""
        try:
            stmt = select(UserModel).where(UserModel.subscription_plan == plan)
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            return [user_model.to_domain_entity() for user_model in user_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get users by subscription plan: {str(e)}")
    
    async def get_users_with_expired_subscriptions(self) -> List[User]:
        """Get users with expired subscriptions."""
        try:
            now = datetime.utcnow()
            stmt = select(UserModel).where(
                and_(
                    UserModel.subscription_expires_at < now,
                    UserModel.status == UserStatus.ACTIVE
                )
            )
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            return [user_model.to_domain_entity() for user_model in user_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get users with expired subscriptions: {str(e)}")
    
    async def get_users_for_notification(self, notification_type: str) -> List[User]:
        """Get users that should receive a specific type of notification."""
        try:
            # This is a placeholder implementation
            # In a real system, you might have notification preferences stored
            stmt = select(UserModel).where(
                and_(
                    UserModel.status == UserStatus.ACTIVE,
                    UserModel.is_email_verified == True
                )
            )
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            return [user_model.to_domain_entity() for user_model in user_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get users for notification: {str(e)}")
    
    async def update_last_login(self, user_id: UUID, login_time: datetime) -> bool:
        """Update user's last login timestamp."""
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    last_login_at=login_time,
                    updated_at=datetime.utcnow()
                )
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to update last login: {str(e)}")
    
    async def update_last_logout(self, user_id: UUID, logout_time: datetime) -> bool:
        """Update user's last logout timestamp."""
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    last_logout_at=logout_time,
                    updated_at=datetime.utcnow()
                )
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to update last logout: {str(e)}")
    
    async def verify_email(self, user_id: UUID) -> None:
        """Mark user's email as verified."""
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    is_email_verified=True,
                    email_verified_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to verify email: {str(e)}")
    
    async def verify_phone(self, user_id: UUID) -> None:
        """Verify user phone number."""
        try:
            # Update user phone verification status
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    is_phone_verified=True,
                    phone_verified_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            result = await self._session.execute(stmt)
            
            if result.rowcount == 0:
                raise NotFoundError(f"User with ID {user_id} not found")
            
            await self._session.commit()
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to verify phone: {str(e)}")
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        try:
            stmt = select(func.count(UserModel.id)).where(UserModel.email == email)
            result = await self._session.execute(stmt)
            count = result.scalar()
            return count > 0
        except Exception as e:
            raise RepositoryError(f"Failed to check email existence: {str(e)}")
    
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username."""
        try:
            stmt = select(func.count(UserModel.id)).where(UserModel.username == username)
            result = await self._session.execute(stmt)
            count = result.scalar()
            return count > 0
        except Exception as e:
            raise RepositoryError(f"Failed to check username existence: {str(e)}")
    
    async def get_users_by_status(self, status: UserStatus) -> List[User]:
        """Get users by status."""
        try:
            stmt = select(UserModel).where(UserModel.status == status)
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            return [user_model.to_domain_entity() for user_model in user_models]
        except Exception as e:
            raise RepositoryError(f"Failed to get users by status: {str(e)}")
    
    async def get_users_created_between(self, start_date: datetime, end_date: datetime) -> List[User]:
        """Get users created between dates."""
        try:
            stmt = select(UserModel).where(
                and_(UserModel.created_at >= start_date, UserModel.created_at <= end_date)
            )
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            return [user_model.to_domain_entity() for user_model in user_models]
        except Exception as e:
            raise RepositoryError(f"Failed to get users by creation date: {str(e)}")
    
    async def get_users_last_login_before(self, date: datetime) -> List[User]:
        """Get users with last login before date."""
        try:
            stmt = select(UserModel).where(UserModel.last_login_at < date)
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            return [user_model.to_domain_entity() for user_model in user_models]
        except Exception as e:
            raise RepositoryError(f"Failed to get users by last login: {str(e)}")
    
    async def increment_login_count(self, user_id: UUID) -> bool:
        """Increment user login count."""
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(login_count=UserModel.login_count + 1)
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to increment login count: {str(e)}")
    
    async def update_user_stats(self, user_id: UUID, stats_update: Dict[str, Any]) -> bool:
        """Update user statistics."""
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(**stats_update)
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to update user stats: {str(e)}")
    
    async def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete user."""
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    status=UserStatus.INACTIVE,
                    deleted_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to soft delete user: {str(e)}")
    
    async def restore_user(self, user_id: UUID) -> bool:
        """Restore soft deleted user."""
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    status=UserStatus.ACTIVE,
                    deleted_at=None,
                    updated_at=datetime.utcnow()
                )
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to restore user: {str(e)}")
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics."""
        try:
            total_users = await self._session.execute(select(func.count(UserModel.id)))
            active_users = await self._session.execute(
                select(func.count(UserModel.id)).where(UserModel.status == UserStatus.ACTIVE)
            )
            inactive_users = await self._session.execute(
                select(func.count(UserModel.id)).where(UserModel.status == UserStatus.INACTIVE)
            )
            
            return {
                "total_users": total_users.scalar(),
                "active_users": active_users.scalar(),
                "inactive_users": inactive_users.scalar()
            }
        except Exception as e:
            raise RepositoryError(f"Failed to get user statistics: {str(e)}")
    
    async def bulk_update_status(self, user_ids: List[UUID], new_status: UserStatus) -> int:
        """Bulk update user status."""
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.id.in_(user_ids))
                .values(
                    status=new_status,
                    updated_at=datetime.utcnow()
                )
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.rowcount
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to bulk update status: {str(e)}")