#!/usr/bin/env python3
"""
Application Repository Interface

Defines the abstract interface for application data access operations.
Implementations should handle database operations for application entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from ..entities.application import Application, ApplicationStatus, ApplicationTier, APIKeyStatus


class ApplicationRepository(ABC):
    """Abstract repository interface for application operations."""

    @abstractmethod
    async def create(self, application: Application) -> Application:
        """Create a new application record.
        
        Args:
            application: The application entity to create
            
        Returns:
            The created application with updated metadata
            
        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, application_id: UUID) -> Optional[Application]:
        """Retrieve an application by its ID.
        
        Args:
            application_id: The unique identifier of the application
            
        Returns:
            The application if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[Application]:
        """Retrieve applications for a specific user.
        
        Args:
            user_id: The user's unique identifier
            limit: Maximum number of applications to return
            offset: Number of applications to skip
            
        Returns:
            List of applications belonging to the user
        """
        pass

    @abstractmethod
    async def get_by_api_key(self, api_key: str) -> Optional[Application]:
        """Retrieve an application by its API key.
        
        Args:
            api_key: The API key to search for
            
        Returns:
            The application if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_name(self, name: str, user_id: UUID) -> Optional[Application]:
        """Retrieve an application by name for a specific user.
        
        Args:
            name: The application name
            user_id: The user's unique identifier
            
        Returns:
            The application if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_status(self, status: ApplicationStatus, limit: int = 50, offset: int = 0) -> List[Application]:
        """Retrieve applications by status.
        
        Args:
            status: The application status to filter by
            limit: Maximum number of applications to return
            offset: Number of applications to skip
            
        Returns:
            List of applications with the specified status
        """
        pass

    @abstractmethod
    async def get_by_tier(self, tier: ApplicationTier, limit: int = 50, offset: int = 0) -> List[Application]:
        """Retrieve applications by tier.
        
        Args:
            tier: The application tier to filter by
            limit: Maximum number of applications to return
            offset: Number of applications to skip
            
        Returns:
            List of applications with the specified tier
        """
        pass

    @abstractmethod
    async def update(self, application: Application) -> Application:
        """Update an existing application.
        
        Args:
            application: The application entity with updated data
            
        Returns:
            The updated application
            
        Raises:
            RepositoryError: If update fails or application not found
        """
        pass

    @abstractmethod
    async def delete(self, application_id: UUID) -> bool:
        """Delete an application by ID.
        
        Args:
            application_id: The unique identifier of the application to delete
            
        Returns:
            True if deletion was successful, False if application not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        pass

    @abstractmethod
    async def list_applications(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[Application]:
        """List applications with optional filtering and sorting.
        
        Args:
            filters: Optional filters to apply (e.g., {'status': 'active', 'tier': 'premium'})
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            limit: Maximum number of applications to return
            offset: Number of applications to skip
            
        Returns:
            List of applications matching the criteria
        """
        pass

    @abstractmethod
    async def count_applications(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count applications with optional filtering.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Total number of applications matching the criteria
        """
        pass

    @abstractmethod
    async def get_usage_stats(self, application_id: UUID) -> Dict[str, Any]:
        """Get usage statistics for an application.
        
        Args:
            application_id: The application's unique identifier
            
        Returns:
            Dictionary containing usage statistics
        """
        pass

    @abstractmethod
    async def update_usage(
        self,
        application_id: UUID,
        requests_count: int = 0,
        tokens_used: int = 0,
        cost_incurred: float = 0.0
    ) -> bool:
        """Update usage statistics for an application.
        
        Args:
            application_id: The application's unique identifier
            requests_count: Number of requests to add
            tokens_used: Number of tokens to add
            cost_incurred: Cost to add
            
        Returns:
            True if update was successful, False if application not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def get_applications_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Application]:
        """Retrieve applications within a date range.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            user_id: Optional user ID to filter by
            limit: Maximum number of applications to return
            offset: Number of applications to skip
            
        Returns:
            List of applications within the date range
        """
        pass

    @abstractmethod
    async def get_expired_api_keys(self, limit: int = 50, offset: int = 0) -> List[Application]:
        """Retrieve applications with expired API keys.
        
        Args:
            limit: Maximum number of applications to return
            offset: Number of applications to skip
            
        Returns:
            List of applications with expired API keys
        """
        pass

    @abstractmethod
    async def update_api_key_status(
        self,
        application_id: UUID,
        api_key: str,
        status: APIKeyStatus
    ) -> bool:
        """Update the status of a specific API key.
        
        Args:
            application_id: The application's unique identifier
            api_key: The API key to update
            status: The new status
            
        Returns:
            True if update was successful, False if not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def revoke_api_key(self, application_id: UUID, api_key: str) -> bool:
        """Revoke a specific API key.
        
        Args:
            application_id: The application's unique identifier
            api_key: The API key to revoke
            
        Returns:
            True if revocation was successful, False if not found
            
        Raises:
            RepositoryError: If revocation fails
        """
        pass

    @abstractmethod
    async def get_active_applications_count(self, user_id: Optional[UUID] = None) -> int:
        """Get count of active applications.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            Number of active applications
        """
        pass

    @abstractmethod
    async def bulk_update_status(
        self,
        application_ids: List[UUID],
        status: ApplicationStatus
    ) -> int:
        """Update status for multiple applications.
        
        Args:
            application_ids: List of application IDs to update
            status: The new status
            
        Returns:
            Number of applications successfully updated
            
        Raises:
            RepositoryError: If bulk update fails
        """
        pass