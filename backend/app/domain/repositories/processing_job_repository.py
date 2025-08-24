#!/usr/bin/env python3
"""
Processing Job Repository Interface

Defines the abstract interface for processing job data access operations.
Implementations should handle database operations for processing job entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from ..entities.processing_job import ProcessingJob, JobStatus, JobPriority, ProcessingStage, AIProvider


class ProcessingJobRepository(ABC):
    """Abstract repository interface for processing job operations."""

    @abstractmethod
    async def create(self, job: ProcessingJob) -> ProcessingJob:
        """Create a new processing job record.
        
        Args:
            job: The processing job entity to create
            
        Returns:
            The created job with updated metadata
            
        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> Optional[ProcessingJob]:
        """Retrieve a processing job by its ID.
        
        Args:
            job_id: The unique identifier of the job
            
        Returns:
            The job if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_credential_id(self, credential_id: UUID) -> Optional[ProcessingJob]:
        """Retrieve a processing job by credential ID.
        
        Args:
            credential_id: The credential's unique identifier
            
        Returns:
            The job if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[ProcessingJob]:
        """Retrieve processing jobs for a specific user.
        
        Args:
            user_id: The user's unique identifier
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of jobs belonging to the user
        """
        pass

    @abstractmethod
    async def get_by_application_id(self, application_id: UUID, limit: int = 50, offset: int = 0) -> List[ProcessingJob]:
        """Retrieve processing jobs for a specific application.
        
        Args:
            application_id: The application's unique identifier
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of jobs for the application
        """
        pass

    @abstractmethod
    async def get_by_status(self, status: JobStatus, limit: int = 50, offset: int = 0) -> List[ProcessingJob]:
        """Retrieve processing jobs by status.
        
        Args:
            status: The job status to filter by
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of jobs with the specified status
        """
        pass

    @abstractmethod
    async def get_by_priority(self, priority: JobPriority, limit: int = 50, offset: int = 0) -> List[ProcessingJob]:
        """Retrieve processing jobs by priority.
        
        Args:
            priority: The job priority to filter by
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of jobs with the specified priority
        """
        pass

    @abstractmethod
    async def get_by_stage(self, stage: ProcessingStage, limit: int = 50, offset: int = 0) -> List[ProcessingJob]:
        """Retrieve processing jobs by current stage.
        
        Args:
            stage: The processing stage to filter by
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of jobs at the specified stage
        """
        pass

    @abstractmethod
    async def get_by_ai_provider(self, provider: AIProvider, limit: int = 50, offset: int = 0) -> List[ProcessingJob]:
        """Retrieve processing jobs by AI provider.
        
        Args:
            provider: The AI provider to filter by
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of jobs using the specified AI provider
        """
        pass

    @abstractmethod
    async def update(self, job: ProcessingJob) -> ProcessingJob:
        """Update an existing processing job.
        
        Args:
            job: The job entity with updated data
            
        Returns:
            The updated job
            
        Raises:
            RepositoryError: If update fails or job not found
        """
        pass

    @abstractmethod
    async def delete(self, job_id: UUID) -> bool:
        """Delete a processing job by ID.
        
        Args:
            job_id: The unique identifier of the job to delete
            
        Returns:
            True if deletion was successful, False if job not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        pass

    @abstractmethod
    async def list_jobs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[ProcessingJob]:
        """List processing jobs with optional filtering and sorting.
        
        Args:
            filters: Optional filters to apply (e.g., {'status': 'running', 'priority': 'high'})
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of jobs matching the criteria
        """
        pass

    @abstractmethod
    async def count_jobs(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count processing jobs with optional filtering.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Total number of jobs matching the criteria
        """
        pass

    @abstractmethod
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get processing queue statistics.
        
        Returns:
            Dictionary containing queue statistics
        """
        pass

    @abstractmethod
    async def get_jobs_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProcessingJob]:
        """Retrieve jobs within a date range.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            user_id: Optional user ID to filter by
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of jobs within the date range
        """
        pass

    @abstractmethod
    async def get_failed_jobs(
        self,
        retry_threshold: int = 3,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProcessingJob]:
        """Retrieve jobs that have failed processing.
        
        Args:
            retry_threshold: Minimum retry count to consider as failed
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of failed jobs
        """
        pass

    @abstractmethod
    async def get_stalled_jobs(
        self,
        stall_threshold_minutes: int = 30,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProcessingJob]:
        """Retrieve jobs that appear to be stalled.
        
        Args:
            stall_threshold_minutes: Minutes without progress to consider stalled
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of stalled jobs
        """
        pass

    @abstractmethod
    async def get_next_jobs_in_queue(
        self,
        limit: int = 10,
        priority_order: bool = True
    ) -> List[ProcessingJob]:
        """Get next jobs to process from the queue.
        
        Args:
            limit: Maximum number of jobs to return
            priority_order: Whether to order by priority
            
        Returns:
            List of jobs ready for processing
        """
        pass

    @abstractmethod
    async def update_job_status(self, job_id: UUID, status: JobStatus) -> bool:
        """Update only the status of a job.
        
        Args:
            job_id: The unique identifier of the job
            status: The new job status
            
        Returns:
            True if update was successful, False if job not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def update_job_stage(self, job_id: UUID, stage: ProcessingStage) -> bool:
        """Update only the processing stage of a job.
        
        Args:
            job_id: The unique identifier of the job
            stage: The new processing stage
            
        Returns:
            True if update was successful, False if job not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def update_job_progress(self, job_id: UUID, progress: float) -> bool:
        """Update the progress of a job.
        
        Args:
            job_id: The unique identifier of the job
            progress: The progress percentage (0.0 to 100.0)
            
        Returns:
            True if update was successful, False if job not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def bulk_update_status(
        self,
        job_ids: List[UUID],
        status: JobStatus
    ) -> int:
        """Update status for multiple jobs.
        
        Args:
            job_ids: List of job IDs to update
            status: The new status
            
        Returns:
            Number of jobs successfully updated
            
        Raises:
            RepositoryError: If bulk update fails
        """
        pass

    @abstractmethod
    async def cleanup_old_jobs(
        self,
        older_than_days: int = 30,
        statuses: Optional[List[JobStatus]] = None
    ) -> int:
        """Clean up old jobs based on age and status.
        
        Args:
            older_than_days: Delete jobs older than this many days
            statuses: Optional list of statuses to filter by
            
        Returns:
            Number of jobs deleted
            
        Raises:
            RepositoryError: If cleanup fails
        """
        pass