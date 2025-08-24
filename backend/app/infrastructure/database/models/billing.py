#!/usr/bin/env python3
"""
Billing Database Model

SQLAlchemy model for billing and cost tracking data persistence.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import relationship

from ..base import BaseModel
from ....domain.entities.billing import (
    TransactionType, TransactionStatus, BillingPeriod, CostCategory, AIProviderCost
)


class BillingModel(BaseModel):
    """Billing database model."""
    
    __tablename__ = "billing"
    
    # Foreign keys
    user_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    application_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Billing period information
    period_type = Column(
        SQLEnum(BillingPeriod),
        nullable=False,
        default=BillingPeriod.MONTHLY,
        index=True
    )
    
    period_start = Column(
        DateTime,
        nullable=False,
        index=True
    )
    
    period_end = Column(
        DateTime,
        nullable=False,
        index=True
    )
    
    # Cost breakdown (stored as JSON)
    cost_breakdown = Column(
        JSONB,
        nullable=False,
        default=dict
    )
    
    # Usage metrics (stored as JSON)
    usage_metrics = Column(
        JSONB,
        nullable=False,
        default=dict
    )
    
    # Transactions (stored as JSON array)
    transactions = Column(
        JSONB,
        nullable=False,
        default=list
    )
    
    # Totals
    total_cost = Column(
        Float,
        nullable=False,
        default=0.0
    )
    
    total_credits = Column(
        Float,
        nullable=False,
        default=0.0
    )
    
    total_usage = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    # Balance information
    opening_balance = Column(
        Float,
        nullable=False,
        default=0.0
    )
    
    closing_balance = Column(
        Float,
        nullable=False,
        default=0.0
    )
    
    # Status flags
    is_finalized = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )
    
    is_paid = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )
    
    is_overdue = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )
    
    # Payment information
    payment_due_date = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    paid_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    payment_method = Column(
        String(50),
        nullable=True
    )
    
    payment_reference = Column(
        String(100),
        nullable=True
    )
    
    # Invoice information
    invoice_number = Column(
        String(50),
        nullable=True,
        unique=True,
        index=True
    )
    
    invoice_generated_at = Column(
        DateTime,
        nullable=True
    )
    
    invoice_sent_at = Column(
        DateTime,
        nullable=True
    )
    
    # Alerts and notifications
    alerts_sent = Column(
        JSONB,
        nullable=False,
        default=list
    )
    
    # Archive information
    archived_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    # Additional metadata
    extra_metadata = Column(
        JSONB,
        nullable=False,
        default=dict
    )
    
    # Relationships
    user = relationship(
        "UserModel",
        back_populates="billing_records"
    )
    
    application = relationship(
        "ApplicationModel",
        back_populates="billing_records"
    )
    
    def to_domain_entity(self):
        """Convert database model to domain entity.
        
        Returns:
            Billing domain entity
        """
        from ....domain.entities.billing import (
            Billing, CostBreakdown, UsageMetrics, Transaction, BillingPeriodData
        )
        
        # Convert cost breakdown
        cost_data = self.cost_breakdown or {}
        cost_breakdown = CostBreakdown(
            ai_processing=cost_data.get('ai_processing', 0.0),
            ocr_processing=cost_data.get('ocr_processing', 0.0),
            storage_costs=cost_data.get('storage_costs', 0.0),
            api_calls=cost_data.get('api_calls', 0.0),
            premium_features=cost_data.get('premium_features', 0.0),
            subscription_fees=cost_data.get('subscription_fees', 0.0),
            provider_costs={
                AIProviderCost(k): v for k, v in cost_data.get('provider_costs', {}).items()
            },
            category_costs={
                CostCategory(k): v for k, v in cost_data.get('category_costs', {}).items()
            }
        )
        
        # Convert usage metrics
        usage_data = self.usage_metrics or {}
        usage_metrics = UsageMetrics(
            total_requests=usage_data.get('total_requests', 0),
            successful_requests=usage_data.get('successful_requests', 0),
            failed_requests=usage_data.get('failed_requests', 0),
            total_processing_time=usage_data.get('total_processing_time', 0.0),
            ai_tokens_used=usage_data.get('ai_tokens_used', 0),
            storage_used_mb=usage_data.get('storage_used_mb', 0.0),
            bandwidth_used_mb=usage_data.get('bandwidth_used_mb', 0.0),
            unique_users=usage_data.get('unique_users', 0),
            peak_concurrent_jobs=usage_data.get('peak_concurrent_jobs', 0),
            average_response_time=usage_data.get('average_response_time', 0.0)
        )
        
        # Convert transactions
        transactions_list = []
        for trans_data in self.transactions or []:
            transaction = Transaction(
                transaction_id=trans_data['transaction_id'],
                type=TransactionType(trans_data['type']),
                status=TransactionStatus(trans_data['status']),
                amount=trans_data['amount'],
                description=trans_data['description'],
                reference=trans_data.get('reference'),
                timestamp=datetime.fromisoformat(trans_data['timestamp']),
                metadata=trans_data.get('metadata', {})
            )
            transactions_list.append(transaction)
        
        # Convert billing period data
        period_data = BillingPeriodData(
            period_type=self.period_type,
            start_date=self.period_start,
            end_date=self.period_end,
            is_current=datetime.utcnow() >= self.period_start and datetime.utcnow() <= self.period_end,
            days_in_period=(self.period_end - self.period_start).days,
            days_remaining=max(0, (self.period_end - datetime.utcnow()).days) if not self.is_finalized else 0
        )
        
        return Billing(
            id=self.id,
            user_id=self.user_id,
            application_id=self.application_id,
            period_data=period_data,
            cost_breakdown=cost_breakdown,
            usage_metrics=usage_metrics,
            transactions=transactions_list,
            total_cost=self.total_cost,
            total_credits=self.total_credits,
            total_usage=self.total_usage,
            opening_balance=self.opening_balance,
            closing_balance=self.closing_balance,
            is_finalized=self.is_finalized,
            is_paid=self.is_paid,
            is_overdue=self.is_overdue,
            payment_due_date=self.payment_due_date,
            paid_at=self.paid_at,
            payment_method=self.payment_method,
            payment_reference=self.payment_reference,
            invoice_number=self.invoice_number,
            invoice_generated_at=self.invoice_generated_at,
            invoice_sent_at=self.invoice_sent_at,
            alerts_sent=self.alerts_sent or [],
            archived_at=self.archived_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.extra_metadata or {}
        )
    
    @classmethod
    def from_domain_entity(cls, billing):
        """Create database model from domain entity.
        
        Args:
            billing: Billing domain entity
            
        Returns:
            BillingModel instance
        """
        # Convert cost breakdown to dict
        cost_dict = {
            'ai_processing': billing.cost_breakdown.ai_processing,
            'ocr_processing': billing.cost_breakdown.ocr_processing,
            'storage_costs': billing.cost_breakdown.storage_costs,
            'api_calls': billing.cost_breakdown.api_calls,
            'premium_features': billing.cost_breakdown.premium_features,
            'subscription_fees': billing.cost_breakdown.subscription_fees,
            'provider_costs': {k.value: v for k, v in billing.cost_breakdown.provider_costs.items()},
            'category_costs': {k.value: v for k, v in billing.cost_breakdown.category_costs.items()}
        }
        
        # Convert usage metrics to dict
        usage_dict = {
            'total_requests': billing.usage_metrics.total_requests,
            'successful_requests': billing.usage_metrics.successful_requests,
            'failed_requests': billing.usage_metrics.failed_requests,
            'total_processing_time': billing.usage_metrics.total_processing_time,
            'ai_tokens_used': billing.usage_metrics.ai_tokens_used,
            'storage_used_mb': billing.usage_metrics.storage_used_mb,
            'bandwidth_used_mb': billing.usage_metrics.bandwidth_used_mb,
            'unique_users': billing.usage_metrics.unique_users,
            'peak_concurrent_jobs': billing.usage_metrics.peak_concurrent_jobs,
            'average_response_time': billing.usage_metrics.average_response_time
        }
        
        # Convert transactions to dict list
        transactions_list = []
        for transaction in billing.transactions:
            trans_dict = {
                'transaction_id': transaction.transaction_id,
                'type': transaction.type.value,
                'status': transaction.status.value,
                'amount': transaction.amount,
                'description': transaction.description,
                'reference': transaction.reference,
                'timestamp': transaction.timestamp.isoformat(),
                'metadata': transaction.metadata
            }
            transactions_list.append(trans_dict)
        
        return cls(
            id=billing.id,
            user_id=billing.user_id,
            application_id=billing.application_id,
            period_type=billing.period_data.period_type,
            period_start=billing.period_data.start_date,
            period_end=billing.period_data.end_date,
            cost_breakdown=cost_dict,
            usage_metrics=usage_dict,
            transactions=transactions_list,
            total_cost=billing.total_cost,
            total_credits=billing.total_credits,
            total_usage=billing.total_usage,
            opening_balance=billing.opening_balance,
            closing_balance=billing.closing_balance,
            is_finalized=billing.is_finalized,
            is_paid=billing.is_paid,
            is_overdue=billing.is_overdue,
            payment_due_date=billing.payment_due_date,
            paid_at=billing.paid_at,
            payment_method=billing.payment_method,
            payment_reference=billing.payment_reference,
            invoice_number=billing.invoice_number,
            invoice_generated_at=billing.invoice_generated_at,
            invoice_sent_at=billing.invoice_sent_at,
            alerts_sent=billing.alerts_sent,
            archived_at=billing.archived_at,
            created_at=billing.created_at,
            updated_at=billing.updated_at,
            extra_metadata=billing.metadata
        )
    
    def update_from_domain_entity(self, billing) -> None:
        """Update database model from domain entity.
        
        Args:
            billing: Billing domain entity
        """
        # Update basic fields
        self.period_type = billing.period_data.period_type
        self.period_start = billing.period_data.start_date
        self.period_end = billing.period_data.end_date
        self.total_cost = billing.total_cost
        self.total_credits = billing.total_credits
        self.total_usage = billing.total_usage
        self.opening_balance = billing.opening_balance
        self.closing_balance = billing.closing_balance
        self.is_finalized = billing.is_finalized
        self.is_paid = billing.is_paid
        self.is_overdue = billing.is_overdue
        self.payment_due_date = billing.payment_due_date
        self.paid_at = billing.paid_at
        self.payment_method = billing.payment_method
        self.payment_reference = billing.payment_reference
        self.invoice_number = billing.invoice_number
        self.invoice_generated_at = billing.invoice_generated_at
        self.invoice_sent_at = billing.invoice_sent_at
        self.alerts_sent = billing.alerts_sent
        self.archived_at = billing.archived_at
        self.extra_metadata = billing.metadata
        
        # Update cost breakdown
        self.cost_breakdown = {
            'ai_processing': billing.cost_breakdown.ai_processing,
            'ocr_processing': billing.cost_breakdown.ocr_processing,
            'storage_costs': billing.cost_breakdown.storage_costs,
            'api_calls': billing.cost_breakdown.api_calls,
            'premium_features': billing.cost_breakdown.premium_features,
            'subscription_fees': billing.cost_breakdown.subscription_fees,
            'provider_costs': {k.value: v for k, v in billing.cost_breakdown.provider_costs.items()},
            'category_costs': {k.value: v for k, v in billing.cost_breakdown.category_costs.items()}
        }
        
        # Update usage metrics
        self.usage_metrics = {
            'total_requests': billing.usage_metrics.total_requests,
            'successful_requests': billing.usage_metrics.successful_requests,
            'failed_requests': billing.usage_metrics.failed_requests,
            'total_processing_time': billing.usage_metrics.total_processing_time,
            'ai_tokens_used': billing.usage_metrics.ai_tokens_used,
            'storage_used_mb': billing.usage_metrics.storage_used_mb,
            'bandwidth_used_mb': billing.usage_metrics.bandwidth_used_mb,
            'unique_users': billing.usage_metrics.unique_users,
            'peak_concurrent_jobs': billing.usage_metrics.peak_concurrent_jobs,
            'average_response_time': billing.usage_metrics.average_response_time
        }
        
        # Update transactions
        transactions_list = []
        for transaction in billing.transactions:
            trans_dict = {
                'transaction_id': transaction.transaction_id,
                'type': transaction.type.value,
                'status': transaction.status.value,
                'amount': transaction.amount,
                'description': transaction.description,
                'reference': transaction.reference,
                'timestamp': transaction.timestamp.isoformat(),
                'metadata': transaction.metadata
            }
            transactions_list.append(trans_dict)
        self.transactions = transactions_list
        
        # Update timestamps
        self.updated_at = billing.updated_at or datetime.utcnow()
    
    @property
    def is_current_period(self) -> bool:
        """Check if this is the current billing period.
        
        Returns:
            True if current period
        """
        now = datetime.utcnow()
        return self.period_start <= now <= self.period_end
    
    @property
    def days_remaining(self) -> int:
        """Get days remaining in billing period.
        
        Returns:
            Days remaining (0 if period ended)
        """
        if self.is_finalized:
            return 0
        
        now = datetime.utcnow()
        if now > self.period_end:
            return 0
        
        return (self.period_end - now).days
    
    @property
    def usage_percentage(self) -> float:
        """Get usage percentage of period.
        
        Returns:
            Usage percentage (0-100)
        """
        total_days = (self.period_end - self.period_start).days
        if total_days == 0:
            return 100.0
        
        elapsed_days = (datetime.utcnow() - self.period_start).days
        return min((elapsed_days / total_days) * 100, 100.0)
    
    @property
    def net_amount(self) -> float:
        """Get net amount (cost - credits).
        
        Returns:
            Net amount
        """
        return self.total_cost - self.total_credits
    
    @property
    def success_rate(self) -> float:
        """Get success rate percentage.
        
        Returns:
            Success rate percentage (0-100)
        """
        usage_data = self.usage_metrics or {}
        total = usage_data.get('total_requests', 0)
        successful = usage_data.get('successful_requests', 0)
        
        if total == 0:
            return 0.0
        
        return (successful / total) * 100
    
    def get_transactions_by_type(self, transaction_type: TransactionType) -> List[Dict[str, Any]]:
        """Get transactions by type.
        
        Args:
            transaction_type: Transaction type to filter by
            
        Returns:
            List of transactions
        """
        if not self.transactions:
            return []
        
        return [
            trans for trans in self.transactions
            if trans.get('type') == transaction_type.value
        ]
    
    def get_cost_by_provider(self, provider: AIProviderCost) -> float:
        """Get cost by AI provider.
        
        Args:
            provider: AI provider
            
        Returns:
            Cost for the provider
        """
        if not self.cost_breakdown:
            return 0.0
        
        provider_costs = self.cost_breakdown.get('provider_costs', {})
        return provider_costs.get(provider.value, 0.0)
    
    def __repr__(self) -> str:
        """String representation of the billing model."""
        return f"<BillingModel(id={self.id}, period={self.period_start.strftime('%Y-%m')}, total_cost={self.total_cost})>"