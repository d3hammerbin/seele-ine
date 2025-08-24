#!/usr/bin/env python3
"""
Billing Repository Implementation

SQLAlchemy implementation of the BillingRepository interface.
Handles database operations for billing entities.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.repositories.billing_repository import BillingRepository
from ...domain.entities.billing import BillingPeriodData, BillingPeriod, TransactionType, Transaction
from ...core.exceptions.base import RepositoryError, NotFoundError
from ..database.models.billing import BillingModel


class BillingRepositoryImpl(BillingRepository):
    """
    SQLAlchemy implementation of BillingRepository.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, billing: BillingPeriodData) -> BillingPeriodData:
        """Create a new billing record in the database."""
        try:
            # Convert domain entity to database model
            billing_model = BillingModel.from_domain_entity(billing)
            
            # Add to session and commit
            self._session.add(billing_model)
            await self._session.commit()
            await self._session.refresh(billing_model)
            
            # Convert back to domain entity
            return billing_model.to_domain_entity()
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to create billing record: {str(e)}")
    
    async def get_by_id(self, billing_id: UUID) -> Optional[BillingPeriodData]:
        """Get billing record by ID."""
        try:
            stmt = select(BillingModel).where(BillingModel.id == billing_id)
            result = await self._session.execute(stmt)
            billing_model = result.scalar_one_or_none()
            
            if billing_model:
                return billing_model.to_domain_entity()
            return None
            
        except Exception as e:
            raise RepositoryError(f"Failed to get billing record: {str(e)}")
    
    async def get_by_user_id(self, user_id: UUID, limit: int = 10, offset: int = 0) -> List[BillingPeriodData]:
        """Get billing records by user ID."""
        try:
            stmt = (
                select(BillingModel)
                .where(BillingModel.user_id == user_id)
                .order_by(BillingModel.period_start.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            billing_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in billing_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get billing records by user: {str(e)}")
    
    async def get_current_billing(self, user_id: UUID, application_id: Optional[UUID] = None) -> Optional[BillingPeriodData]:
        """Get current billing period for user and application."""
        try:
            now = datetime.utcnow()
            stmt = (
                select(BillingModel)
                .where(
                    and_(
                        BillingModel.user_id == user_id,
                        BillingModel.application_id == application_id,
                        BillingModel.period_start <= now,
                        BillingModel.period_end >= now
                    )
                )
            )
            result = await self._session.execute(stmt)
            billing_model = result.scalar_one_or_none()
            
            if billing_model:
                return billing_model.to_domain_entity()
            return None
            
        except Exception as e:
            raise RepositoryError(f"Failed to get current billing: {str(e)}")
    
    async def get_by_period(self, user_id: UUID, period_start: datetime, period_end: datetime, application_id: Optional[UUID] = None) -> List[BillingPeriodData]:
        """Get billing records by period."""
        try:
            conditions = [
                BillingModel.user_id == user_id,
                or_(
                    and_(
                        BillingModel.period_start >= period_start,
                        BillingModel.period_start <= period_end
                    ),
                    and_(
                        BillingModel.period_end >= period_start,
                        BillingModel.period_end <= period_end
                    ),
                    and_(
                        BillingModel.period_start <= period_start,
                        BillingModel.period_end >= period_end
                    )
                )
            ]
            
            if application_id:
                conditions.append(BillingModel.application_id == application_id)
            
            stmt = (
                select(BillingModel)
                .where(and_(*conditions))
                .order_by(BillingModel.period_start.desc())
            )
            result = await self._session.execute(stmt)
            billing_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in billing_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get billing records by period: {str(e)}")
    
    async def update(self, billing: BillingPeriodData) -> BillingPeriodData:
        """Update billing record."""
        try:
            # Get existing model
            stmt = select(BillingModel).where(BillingModel.id == billing.id)
            result = await self._session.execute(stmt)
            billing_model = result.scalar_one_or_none()
            
            if not billing_model:
                raise NotFoundError(f"Billing record not found: {billing.id}")
            
            # Update model from domain entity
            billing_model.update_from_domain_entity(billing)
            
            # Commit changes
            await self._session.commit()
            await self._session.refresh(billing_model)
            
            return billing_model.to_domain_entity()
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to update billing record: {str(e)}")
    
    async def delete(self, billing_id: UUID) -> bool:
        """Delete billing record."""
        try:
            stmt = delete(BillingModel).where(BillingModel.id == billing_id)
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to delete billing record: {str(e)}")
    
    async def get_unpaid_billings(self, user_id: Optional[UUID] = None) -> List[BillingPeriodData]:
        """Get unpaid billing records."""
        try:
            conditions = [BillingModel.is_paid == False]
            
            if user_id:
                conditions.append(BillingModel.user_id == user_id)
            
            stmt = (
                select(BillingModel)
                .where(and_(*conditions))
                .order_by(BillingModel.payment_due_date.asc())
            )
            result = await self._session.execute(stmt)
            billing_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in billing_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get unpaid billings: {str(e)}")
    
    async def get_overdue_billings(self, user_id: Optional[UUID] = None) -> List[BillingPeriodData]:
        """Get overdue billing records."""
        try:
            now = datetime.utcnow()
            conditions = [
                BillingModel.is_paid == False,
                BillingModel.payment_due_date < now
            ]
            
            if user_id:
                conditions.append(BillingModel.user_id == user_id)
            
            stmt = (
                select(BillingModel)
                .where(and_(*conditions))
                .order_by(BillingModel.payment_due_date.asc())
            )
            result = await self._session.execute(stmt)
            billing_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in billing_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get overdue billings: {str(e)}")
    
    async def get_billing_statistics(self, user_id: Optional[UUID] = None, period_start: Optional[datetime] = None, period_end: Optional[datetime] = None) -> Dict[str, Any]:
        """Get billing statistics."""
        try:
            conditions = []
            
            if user_id:
                conditions.append(BillingModel.user_id == user_id)
            
            if period_start:
                conditions.append(BillingModel.period_start >= period_start)
            
            if period_end:
                conditions.append(BillingModel.period_end <= period_end)
            
            base_query = select(BillingModel)
            if conditions:
                base_query = base_query.where(and_(*conditions))
            
            # Total records
            count_stmt = select(func.count(BillingModel.id)).select_from(base_query.subquery())
            count_result = await self._session.execute(count_stmt)
            total_records = count_result.scalar()
            
            # Sum statistics
            sum_stmt = select(
                func.sum(BillingModel.total_cost).label('total_cost'),
                func.sum(BillingModel.total_credits).label('total_credits'),
                func.sum(BillingModel.total_usage).label('total_usage'),
                func.count(func.case([(BillingModel.is_paid == True, 1)])).label('paid_count'),
                func.count(func.case([(BillingModel.is_paid == False, 1)])).label('unpaid_count')
            ).select_from(base_query.subquery())
            
            sum_result = await self._session.execute(sum_stmt)
            stats = sum_result.first()
            
            return {
                'total_records': total_records,
                'total_cost': float(stats.total_cost or 0),
                'total_credits': float(stats.total_credits or 0),
                'total_usage': float(stats.total_usage or 0),
                'paid_count': stats.paid_count or 0,
                'unpaid_count': stats.unpaid_count or 0,
                'payment_rate': (stats.paid_count / total_records * 100) if total_records > 0 else 0
            }
            
        except Exception as e:
            raise RepositoryError(f"Failed to get billing statistics: {str(e)}")