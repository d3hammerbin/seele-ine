#!/usr/bin/env python3
"""
Billing Domain Service

Contains business logic for billing and cost management operations.
Handles complex billing-related business rules and validations.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP

from ..entities.billing import (
    BillingPeriodData, Transaction, TransactionType, TransactionStatus, BillingPeriod, 
    CostCategory, AIProviderCost, CostBreakdown, UsageMetrics
)
from ..entities.user import User, SubscriptionPlan
from ..entities.application import Application
from ..entities.processing_job import ProcessingJob, AIProvider
from ..repositories.billing_repository import BillingRepository
from ..repositories.user_repository import UserRepository
from ..repositories.application_repository import ApplicationRepository
from ..repositories.processing_job_repository import ProcessingJobRepository
from ...core.exceptions.base import (
    ValidationException, BusinessLogicError, NotFoundError, AuthorizationException,
    BillingError, InsufficientCreditsError
)


class BillingService:
    """Domain service for billing business logic."""

    # Cost configuration per AI provider (USD per 1K tokens)
    AI_PROVIDER_COSTS = {
        AIProvider.OPENAI: {
            'input_cost_per_1k': Decimal('0.0015'),
            'output_cost_per_1k': Decimal('0.002'),
            'image_cost_per_request': Decimal('0.01')
        },
        AIProvider.DEEPSEEK: {
            'input_cost_per_1k': Decimal('0.0007'),
            'output_cost_per_1k': Decimal('0.0014'),
            'image_cost_per_request': Decimal('0.005')
        },
        AIProvider.GEMINI: {
            'input_cost_per_1k': Decimal('0.001'),
            'output_cost_per_1k': Decimal('0.002'),
            'image_cost_per_request': Decimal('0.008')
        },
        AIProvider.CLAUDE: {
            'input_cost_per_1k': Decimal('0.0015'),
            'output_cost_per_1k': Decimal('0.0075'),
            'image_cost_per_request': Decimal('0.012')
        }
    }
    
    # Subscription plan credits (monthly)
    SUBSCRIPTION_CREDITS = {
        SubscriptionPlan.FREE: Decimal('0'),
        SubscriptionPlan.BASIC: Decimal('10'),
        SubscriptionPlan.PREMIUM: Decimal('50'),
        SubscriptionPlan.ENTERPRISE: Decimal('200')
    }
    
    # Minimum balance thresholds for alerts
    LOW_BALANCE_THRESHOLDS = {
        SubscriptionPlan.FREE: Decimal('0'),
        SubscriptionPlan.BASIC: Decimal('2'),
        SubscriptionPlan.PREMIUM: Decimal('10'),
        SubscriptionPlan.ENTERPRISE: Decimal('50')
    }

    def __init__(
        self,
        billing_repository: BillingRepository,
        user_repository: UserRepository,
        application_repository: ApplicationRepository,
        processing_job_repository: ProcessingJobRepository
    ):
        self._billing_repository = billing_repository
        self._user_repository = user_repository
        self._application_repository = application_repository
        self._processing_job_repository = processing_job_repository

    async def create_billing_period(
        self,
        user_id: UUID,
        application_id: UUID,
        period: BillingPeriod = BillingPeriod.MONTHLY
    ) -> BillingPeriodData:
        """Create a new billing period.
        
        Args:
            user_id: User's unique identifier
            application_id: Application's unique identifier
            period: Billing period type
            
        Returns:
            The created billing record
            
        Raises:
            ValidationException: If validation fails
            BusinessLogicError: If business rules are violated
            NotFoundError: If entities not found
        """
        # Validate entities exist
        await self._validate_billing_entities(user_id, application_id)
        
        # Check if current period already exists
        current_billing = await self._billing_repository.get_current_period(
            user_id, application_id, period
        )
        
        if current_billing:
            raise BusinessLogicError("Current billing period already exists")
        
        # Create new billing period
        billing = BillingPeriodData(
            user_id=user_id,
            application_id=application_id,
            period_type=period
        )

        return await self._billing_repository.create(billing)

    async def record_processing_cost(
        self,
        user_id: UUID,
        application_id: UUID,
        processing_job_id: UUID,
        ai_provider: AIProvider,
        input_tokens: int,
        output_tokens: int,
        image_requests: int = 0,
        additional_costs: Optional[Dict[str, Decimal]] = None
    ) -> BillingPeriodData:
        """Record cost for a processing job.
        
        Args:
            user_id: User's unique identifier
            application_id: Application's unique identifier
            processing_job_id: Processing job's unique identifier
            ai_provider: AI provider used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            image_requests: Number of image processing requests
            additional_costs: Optional additional costs
            
        Returns:
            Updated billing record
            
        Raises:
            NotFoundError: If entities not found
            BillingError: If billing operation fails
        """
        # Get or create current billing period
        billing = await self._get_or_create_current_billing(
            user_id, application_id
        )
        
        # Calculate costs
        cost_breakdown = self._calculate_processing_costs(
            ai_provider, input_tokens, output_tokens, image_requests, additional_costs
        )
        
        # Check user balance before recording cost
        user_balance = await self.get_user_balance(user_id)
        if user_balance < cost_breakdown['total_cost']:
            raise InsufficientCreditsError(
                f"Insufficient balance. Required: ${cost_breakdown['total_cost']}, Available: ${user_balance}"
            )
        
        # Record the cost
        billing.add_cost(
            category=CostCategory.AI_PROCESSING,
            amount=cost_breakdown['total_cost'],
            description=f"Processing job {processing_job_id}",
            metadata={
                'processing_job_id': str(processing_job_id),
                'ai_provider': ai_provider.value,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'image_requests': image_requests,
                'cost_breakdown': cost_breakdown
            }
        )
        
        # Update usage metrics
        billing.usage_metrics.total_requests += 1
        billing.usage_metrics.total_tokens += input_tokens + output_tokens
        billing.usage_metrics.ai_provider_usage[ai_provider] = (
            billing.usage_metrics.ai_provider_usage.get(ai_provider, 0) + 1
        )
        
        return await self._billing_repository.update(billing)

    async def add_credits(
        self,
        user_id: UUID,
        amount: Decimal,
        transaction_type: TransactionType = TransactionType.CREDIT,
        description: str = "Credit purchase",
        reference_id: Optional[str] = None
    ) -> BillingPeriodData:
        """Add credits to user's account.
        
        Args:
            user_id: User's unique identifier
            amount: Amount to add
            transaction_type: Type of transaction
            description: Transaction description
            reference_id: Optional reference ID
            
        Returns:
            Updated billing record
            
        Raises:
            ValidationException: If validation fails
            NotFoundError: If user not found
        """
        if amount <= 0:
            raise ValidationException("Credit amount must be positive")
        
        # Get user's primary application or create one
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Get user's applications
        applications = await self._application_repository.get_by_user_id(user_id)
        if not applications:
            raise BusinessLogicError("User has no applications")
        
        # Use first active application
        application = next((app for app in applications if app.is_active), applications[0])
        
        # Get or create current billing period
        billing = await self._get_or_create_current_billing(user_id, application.id)
        
        # Add transaction
        billing.add_transaction(
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            reference_id=reference_id
        )
        
        return await self._billing_repository.update(billing)

    async def process_subscription_credits(
        self,
        user_id: UUID
    ) -> List[BillingPeriodData]:
        """Process monthly subscription credits for user.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of updated billing records
            
        Raises:
            NotFoundError: If user not found
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Get subscription credits
        credits = self.SUBSCRIPTION_CREDITS.get(user.subscription_plan, Decimal('0'))
        if credits <= 0:
            return []
        
        # Get all user applications
        applications = await self._application_repository.get_by_user_id(user_id)
        updated_billings = []
        
        for application in applications:
            if not application.is_active:
                continue
                
            try:
                billing = await self._get_or_create_current_billing(user_id, application.id)
                
                # Add subscription credits
                billing.add_transaction(
                    transaction_type=TransactionType.SUBSCRIPTION_CREDIT,
                    amount=credits,
                    description=f"Monthly {user.subscription_plan.value} subscription credits"
                )
                
                updated_billing = await self._billing_repository.update(billing)
                updated_billings.append(updated_billing)
                
            except Exception as e:
                # Log error but continue with other applications
                continue
        
        return updated_billings

    async def get_user_balance(
        self,
        user_id: UUID,
        application_id: Optional[UUID] = None
    ) -> Decimal:
        """Get user's current balance.
        
        Args:
            user_id: User's unique identifier
            application_id: Optional application filter
            
        Returns:
            Current balance
            
        Raises:
            NotFoundError: If user not found
        """
        return await self._billing_repository.get_user_balance(user_id, application_id)

    async def get_billing_summary(
        self,
        user_id: UUID,
        application_id: Optional[UUID] = None,
        period: Optional[BillingPeriod] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get billing summary for user.
        
        Args:
            user_id: User's unique identifier
            application_id: Optional application filter
            period: Optional billing period filter
            date_range: Optional date range filter
            
        Returns:
            Billing summary dictionary
            
        Raises:
            NotFoundError: If user not found
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Get billing records
        billing_records = await self._billing_repository.get_by_user_id(
            user_id, application_id, period
        )
        
        if date_range:
            start_date, end_date = date_range
            billing_records = [
                record for record in billing_records
                if start_date <= record.period_start <= end_date
            ]
        
        # Calculate summary
        total_costs = sum(record.total_cost for record in billing_records)
        total_credits = sum(
            sum(t.amount for t in record.transactions if t.amount > 0)
            for record in billing_records
        )
        total_usage = sum(
            record.usage_metrics.total_requests for record in billing_records
        )
        
        # Get current balance
        current_balance = await self.get_user_balance(user_id, application_id)
        
        # Check for low balance alert
        threshold = self.LOW_BALANCE_THRESHOLDS.get(user.subscription_plan, Decimal('0'))
        low_balance_alert = current_balance <= threshold
        
        return {
            'user_id': user_id,
            'application_id': application_id,
            'current_balance': float(current_balance),
            'total_costs': float(total_costs),
            'total_credits': float(total_credits),
            'total_usage': total_usage,
            'billing_periods': len(billing_records),
            'low_balance_alert': low_balance_alert,
            'subscription_plan': user.subscription_plan.value,
            'monthly_credits': float(self.SUBSCRIPTION_CREDITS.get(user.subscription_plan, Decimal('0')))
        }

    async def get_cost_breakdown(
        self,
        user_id: UUID,
        application_id: Optional[UUID] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get detailed cost breakdown.
        
        Args:
            user_id: User's unique identifier
            application_id: Optional application filter
            date_range: Optional date range filter
            
        Returns:
            Cost breakdown dictionary
        """
        cost_breakdown = await self._billing_repository.get_cost_breakdown(
            user_id, application_id, date_range
        )
        
        # Add AI provider costs
        ai_provider_costs = await self._billing_repository.get_ai_provider_costs(
            user_id, application_id, date_range
        )
        
        cost_breakdown['ai_provider_costs'] = ai_provider_costs
        
        return cost_breakdown

    async def generate_invoice(
        self,
        user_id: UUID,
        application_id: UUID,
        billing_period_id: UUID
    ) -> Dict[str, Any]:
        """Generate invoice for a billing period.
        
        Args:
            user_id: User's unique identifier
            application_id: Application's unique identifier
            billing_period_id: Billing period's unique identifier
            
        Returns:
            Invoice data dictionary
            
        Raises:
            NotFoundError: If entities not found
            AuthorizationException: If user doesn't own the billing record
        """
        billing = await self._billing_repository.get_by_id(billing_period_id)
        if not billing:
            raise NotFoundError("Billing period not found")
        
        if billing.user_id != user_id or billing.application_id != application_id:
            raise AuthorizationException("User does not own this billing record")
        
        # Get user and application details
        user = await self._user_repository.get_by_id(user_id)
        application = await self._application_repository.get_by_id(application_id)
        
        # Generate invoice data
        invoice_data = await self._billing_repository.generate_invoice_data(
            billing_period_id
        )
        
        invoice_data.update({
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name
            },
            'application': {
                'id': str(application.id),
                'name': application.name,
                'tier': application.tier.value
            },
            'billing_period': {
                'id': str(billing.id),
                'period': billing.period.value,
                'start_date': billing.period_start.isoformat(),
                'end_date': billing.period_end.isoformat()
            }
        })
        
        return invoice_data

    async def check_billing_alerts(
        self,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Check for billing alerts.
        
        Args:
            user_id: Optional user filter
            
        Returns:
            List of billing alerts
        """
        return await self._billing_repository.get_billing_alerts(user_id)

    async def archive_old_billing_records(
        self,
        months_old: int = 12
    ) -> int:
        """Archive old billing records.
        
        Args:
            months_old: Number of months old to archive
            
        Returns:
            Number of archived records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=months_old * 30)
        return await self._billing_repository.archive_old_records(cutoff_date)

    async def _validate_billing_entities(
        self,
        user_id: UUID,
        application_id: UUID
    ) -> None:
        """Validate entities for billing operations.
        
        Args:
            user_id: User's unique identifier
            application_id: Application's unique identifier
            
        Raises:
            NotFoundError: If entities not found
            AuthorizationException: If user doesn't own the application
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        if application.user_id != user_id:
            raise AuthorizationException("User does not own this application")

    async def _get_or_create_current_billing(
        self,
        user_id: UUID,
        application_id: UUID,
        period: BillingPeriod = BillingPeriod.MONTHLY
    ) -> BillingPeriodData:
        """Get or create current billing period.
        
        Args:
            user_id: User's unique identifier
            application_id: Application's unique identifier
            period: Billing period type
            
        Returns:
            Current billing record
        """
        # Try to get current billing period
        billing = await self._billing_repository.get_current_period(
            user_id, application_id, period
        )
        
        if not billing:
            # Create new billing period
            billing = BillingPeriodData(
                user_id=user_id,
                application_id=application_id,
                period_type=period
            )
            billing = await self._billing_repository.create(billing)
        
        return billing

    def _calculate_processing_costs(
        self,
        ai_provider: AIProvider,
        input_tokens: int,
        output_tokens: int,
        image_requests: int = 0,
        additional_costs: Optional[Dict[str, Decimal]] = None
    ) -> Dict[str, Decimal]:
        """Calculate processing costs.
        
        Args:
            ai_provider: AI provider used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            image_requests: Number of image processing requests
            additional_costs: Optional additional costs
            
        Returns:
            Cost breakdown dictionary
        """
        provider_costs = self.AI_PROVIDER_COSTS.get(ai_provider, {
            'input_cost_per_1k': Decimal('0.001'),
            'output_cost_per_1k': Decimal('0.002'),
            'image_cost_per_request': Decimal('0.01')
        })
        
        # Calculate token costs
        input_cost = (Decimal(input_tokens) / 1000) * provider_costs['input_cost_per_1k']
        output_cost = (Decimal(output_tokens) / 1000) * provider_costs['output_cost_per_1k']
        image_cost = Decimal(image_requests) * provider_costs['image_cost_per_request']
        
        # Round to 6 decimal places
        input_cost = input_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
        output_cost = output_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
        image_cost = image_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
        
        total_cost = input_cost + output_cost + image_cost
        
        # Add additional costs if provided
        if additional_costs:
            for cost_name, cost_amount in additional_costs.items():
                total_cost += cost_amount
        
        return {
            'input_cost': input_cost,
            'output_cost': output_cost,
            'image_cost': image_cost,
            'additional_costs': additional_costs or {},
            'total_cost': total_cost,
            'ai_provider': ai_provider.value
        }