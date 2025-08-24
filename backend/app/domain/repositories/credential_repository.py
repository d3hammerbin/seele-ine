#!/usr/bin/env python3
"""
Credential Repository Interface

Defines the abstract interface for credential data access operations.
Implementations should handle database operations for credential entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from ..entities.credential import Credential, CredentialType, ProcessingStatus


class CredentialRepository(ABC):
    """Abstract repository interface for credential operations."""

    @abstractmethod
    async def create(self, credential: Credential) -> Credential:
        """Create a new credential record.
        
        Args:
            credential: The credential entity to create
            
        Returns:
            The created credential with updated metadata
            
        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, credential_id: UUID) -> Optional[Credential]:
        """Retrieve a credential by its ID.
        
        Args:
            credential_id: The unique identifier of the credential
            
        Returns:
            The credential if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[Credential]:
        """Retrieve credentials for a specific user.
        
        Args:
            user_id: The user's unique identifier
            limit: Maximum number of credentials to return
            offset: Number of credentials to skip
            
        Returns:
            List of credentials belonging to the user
        """
        pass

    @abstractmethod
    async def get_by_application_id(self, application_id: UUID, limit: int = 50, offset: int = 0) -> List[Credential]:
        """Retrieve credentials processed by a specific application.
        
        Args:
            application_id: The application's unique identifier
            limit: Maximum number of credentials to return
            offset: Number of credentials to skip
            
        Returns:
            List of credentials processed by the application
        """
        pass

    @abstractmethod
    async def get_by_status(self, status: ProcessingStatus, limit: int = 50, offset: int = 0) -> List[Credential]:
        """Retrieve credentials by processing status.
        
        Args:
            status: The processing status to filter by
            limit: Maximum number of credentials to return
            offset: Number of credentials to skip
            
        Returns:
            List of credentials with the specified status
        """
        pass

    @abstractmethod
    async def get_by_type(self, credential_type: CredentialType, limit: int = 50, offset: int = 0) -> List[Credential]:
        """Retrieve credentials by type.
        
        Args:
            credential_type: The credential type to filter by
            limit: Maximum number of credentials to return
            offset: Number of credentials to skip
            
        Returns:
            List of credentials of the specified type
        """
        pass

    @abstractmethod
    async def update(self, credential: Credential) -> Credential:
        """Update an existing credential.
        
        Args:
            credential: The credential entity with updated data
            
        Returns:
            The updated credential
            
        Raises:
            RepositoryError: If update fails or credential not found
        """
        pass

    @abstractmethod
    async def delete(self, credential_id: UUID) -> bool:
        """Delete a credential by ID.
        
        Args:
            credential_id: The unique identifier of the credential to delete
            
        Returns:
            True if deletion was successful, False if credential not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        pass

    @abstractmethod
    async def list_credentials(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[Credential]:
        """List credentials with optional filtering and sorting.
        
        Args:
            filters: Optional filters to apply (e.g., {'status': 'completed', 'user_id': uuid})
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            limit: Maximum number of credentials to return
            offset: Number of credentials to skip
            
        Returns:
            List of credentials matching the criteria
        """
        pass

    @abstractmethod
    async def count_credentials(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count credentials with optional filtering.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Total number of credentials matching the criteria
        """
        pass

    @abstractmethod
    async def get_processing_stats(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get processing statistics.
        
        Args:
            user_id: Optional user ID to filter stats
            
        Returns:
            Dictionary containing processing statistics
        """
        pass

    @abstractmethod
    async def get_credentials_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Credential]:
        """Retrieve credentials within a date range.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            user_id: Optional user ID to filter by
            limit: Maximum number of credentials to return
            offset: Number of credentials to skip
            
        Returns:
            List of credentials within the date range
        """
        pass

    @abstractmethod
    async def get_failed_credentials(
        self,
        retry_count_threshold: int = 3,
        limit: int = 50,
        offset: int = 0
    ) -> List[Credential]:
        """Retrieve credentials that have failed processing.
        
        Args:
            retry_count_threshold: Minimum retry count to consider as failed
            limit: Maximum number of credentials to return
            offset: Number of credentials to skip
            
        Returns:
            List of failed credentials
        """
        pass

    @abstractmethod
    async def update_processing_status(self, credential_id: UUID, status: ProcessingStatus) -> bool:
        """Update only the processing status of a credential.
        
        Args:
            credential_id: The unique identifier of the credential
            status: The new processing status
            
        Returns:
            True if update was successful, False if credential not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def bulk_update_status(
        self,
        credential_ids: List[UUID],
        status: ProcessingStatus
    ) -> int:
        """Update processing status for multiple credentials.
        
        Args:
            credential_ids: List of credential IDs to update
            status: The new processing status
            
        Returns:
            Number of credentials successfully updated
            
        Raises:
            RepositoryError: If bulk update fails
        """
        pass