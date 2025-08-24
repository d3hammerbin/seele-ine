#!/usr/bin/env python3
"""
Billing Repository Interface

Defines the abstract interface for billing data access operations.
Implementations should handle database operations for billing entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from ..entities.billing import (
    BillingPeriodData, Transaction, TransactionType, TransactionStatus, BillingPeriod, 
    CostCategory, AIProviderCost, CostBreakdown, UsageMetrics
)


class BillingRepository(ABC):
    """Abstract repository interface for billing operations."""

    @abstractmethod
    async def create(self, billing: BillingPeriodData) -> BillingPeriodData:
        """Create a new billing record.
        
        Args:
            billing: The billing entity to create
            
        Returns:
            The created billing record with updated metadata
            
        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, billing_id: UUID) -> Optional[BillingPeriodData]:
        """Retrieve a billing record by its ID.
        
        Args:
            billing_id: The unique identifier of the billing record
            
        Returns:
            The billing record if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[BillingPeriodData]:
        """Retrieve billing records for a specific user.
        
        Args:
            user_id: The user's unique identifier
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of billing records belonging to the user
        """
        pass

    @abstractmethod
    async def get_by_application_id(self, application_id: UUID, limit: int = 50, offset: int = 0) -> List[BillingPeriodData]:
        """Retrieve billing records for a specific application.
        
        Args:
            application_id: The application's unique identifier
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of billing records for the application
        """
        pass

    @abstractmethod
    async def get_by_period(
        self,
        period: BillingPeriod,
        year: int,
        month: Optional[int] = None,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[BillingPeriodData]:
        """Retrieve billing records for a specific period.
        
        Args:
            period: The billing period type
            year: The year
            month: The month (required for monthly periods)
            user_id: Optional user ID to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of billing records for the period
        """
        pass

    @abstractmethod
    async def get_current_period_billing(self, user_id: UUID) -> Optional[BillingPeriodData]:
        """Get the current billing period record for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            The current billing record if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, billing: BillingPeriodData) -> BillingPeriodData:
        """Update an existing billing record.
        
        Args:
            billing: The billing entity with updated data
            
        Returns:
            The updated billing record
            
        Raises:
            RepositoryError: If update fails or record not found
        """
        pass

    @abstractmethod
    async def delete(self, billing_id: UUID) -> bool:
        """Delete a billing record by ID.
        
        Args:
            billing_id: The unique identifier of the record to delete
            
        Returns:
            True if deletion was successful, False if record not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        pass

    @abstractmethod
    async def list_billing_records(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "period_start",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[BillingPeriodData]:
        """List billing records with optional filtering and sorting.
        
        Args:
            filters: Optional filters to apply
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of billing records matching the criteria
        """
        pass

    @abstractmethod
    async def count_billing_records(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count billing records with optional filtering.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Total number of records matching the criteria
        """
        pass

    @abstractmethod
    async def add_cost(
        self,
        billing_id: UUID,
        category: CostCategory,
        amount: Decimal,
        provider: Optional[AIProviderCost] = None,
        description: Optional[str] = None
    ) -> bool:
        """Add a cost to a billing record.
        
        Args:
            billing_id: The billing record ID
            category: The cost category
            amount: The cost amount
            provider: Optional AI provider for AI-related costs
            description: Optional cost description
            
        Returns:
            True if cost was added successfully
            
        Raises:
            RepositoryError: If operation fails
        """
        pass

    @abstractmethod
    async def add_transaction(
        self,
        billing_id: UUID,
        transaction_type: TransactionType,
        amount: Decimal,
        description: Optional[str] = None,
        reference_id: Optional[str] = None
    ) -> bool:
        """Add a transaction to a billing record.
        
        Args:
            billing_id: The billing record ID
            transaction_type: The type of transaction
            amount: The transaction amount
            description: Optional transaction description
            reference_id: Optional external reference ID
            
        Returns:
            True if transaction was added successfully
            
        Raises:
            RepositoryError: If operation fails
        """
        pass

    @abstractmethod
    async def update_transaction_status(
        self,
        billing_id: UUID,
        transaction_id: UUID,
        status: TransactionStatus
    ) -> bool:
        """Update the status of a transaction.
        
        Args:
            billing_id: The billing record ID
            transaction_id: The transaction ID
            status: The new transaction status
            
        Returns:
            True if update was successful
            
        Raises:
            RepositoryError: If operation fails
        """
        pass

    @abstractmethod
    async def get_cost_breakdown(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get detailed cost breakdown for a user within a date range.
        
        Args:
            user_id: The user's unique identifier
            start_date: Start of the date range
            end_date: End of the date range
            
        Returns:
            Dictionary containing detailed cost breakdown
        """
        pass

    @abstractmethod
    async def get_usage_summary(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get usage summary for a user within a date range.
        
        Args:
            user_id: The user's unique identifier
            start_date: Start of the date range
            end_date: End of the date range
            
        Returns:
            Dictionary containing usage summary
        """
        pass

    @abstractmethod
    async def get_provider_costs(
        self,
        provider: AIProviderCost,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get costs by AI provider within a date range.
        
        Args:
            provider: The AI provider
            start_date: Start of the date range
            end_date: End of the date range
            user_id: Optional user ID to filter by
            
        Returns:
            List of cost records for the provider
        """
        pass

    @abstractmethod
    async def get_monthly_totals(
        self,
        user_id: UUID,
        year: int,
        months: Optional[List[int]] = None
    ) -> Dict[int, Decimal]:
        """Get monthly cost totals for a user.
        
        Args:
            user_id: The user's unique identifier
            year: The year
            months: Optional list of months to include
            
        Returns:
            Dictionary mapping month numbers to total costs
        """
        pass

    @abstractmethod
    async def get_pending_transactions(
        self,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get pending transactions.
        
        Args:
            user_id: Optional user ID to filter by
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of pending transactions
        """
        pass

    @abstractmethod
    async def calculate_user_balance(self, user_id: UUID) -> Decimal:
        """Calculate the current balance for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            The user's current balance
        """
        pass

    @abstractmethod
    async def get_billing_alerts(
        self,
        user_id: UUID,
        threshold_percentage: float = 80.0
    ) -> List[Dict[str, Any]]:
        """Get billing alerts for a user based on usage thresholds.
        
        Args:
            user_id: The user's unique identifier
            threshold_percentage: Percentage threshold for alerts
            
        Returns:
            List of billing alerts
        """
        pass

    @abstractmethod
    async def archive_old_records(
        self,
        older_than_months: int = 12,
        keep_summary: bool = True
    ) -> int:
        """Archive old billing records.
        
        Args:
            older_than_months: Archive records older than this many months
            keep_summary: Whether to keep summary data
            
        Returns:
            Number of records archived
            
        Raises:
            RepositoryError: If archiving fails
        """
        pass

    @abstractmethod
    async def generate_invoice_data(
        self,
        user_id: UUID,
        billing_period_id: UUID
    ) -> Dict[str, Any]:
        """Generate invoice data for a billing period.
        
        Args:
            user_id: The user's unique identifier
            billing_period_id: The billing period ID
            
        Returns:
            Dictionary containing invoice data
        """
        pass