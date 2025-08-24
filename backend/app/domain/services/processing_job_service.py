#!/usr/bin/env python3
"""
Processing Job Domain Service

Contains business logic for processing job operations.
Handles complex job-related business rules and validations.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import asyncio

from ..entities.processing_job import (
    ProcessingJob, JobStatus, JobPriority, ProcessingStage, AIProvider
)
from ..entities.credential import Credential, ProcessingStatus
from ..entities.application import Application
from ..entities.user import User
from ..repositories.processing_job_repository import ProcessingJobRepository
from ..repositories.credential_repository import CredentialRepository
from ..repositories.application_repository import ApplicationRepository
from ..repositories.user_repository import UserRepository
from ...core.exceptions.base import (
    ValidationException, BusinessLogicError, NotFoundError, AuthorizationException,
    AIProviderError, RateLimitError
)


class ProcessingJobService:
    """Domain service for processing job business logic."""

    # Job configuration
    MAX_RETRY_ATTEMPTS = 3
    JOB_TIMEOUT_MINUTES = 30
    PRIORITY_QUEUE_SIZE = 100
    
    # Processing stage timeouts (in minutes)
    STAGE_TIMEOUTS = {
        ProcessingStage.QUEUED: 60,
        ProcessingStage.PREPROCESSING: 10,
        ProcessingStage.OCR_EXTRACTION: 15,
        ProcessingStage.QR_EXTRACTION: 5,
        ProcessingStage.AI_PROCESSING: 20,
        ProcessingStage.VALIDATION: 5,
        ProcessingStage.POSTPROCESSING: 10
    }
    
    # AI Provider priority order for fallback
    AI_PROVIDER_FALLBACK = [
        AIProvider.OPENAI,
        AIProvider.DEEPSEEK,
        AIProvider.GEMINI,
        AIProvider.CLAUDE
    ]

    def __init__(
        self,
        processing_job_repository: ProcessingJobRepository,
        credential_repository: CredentialRepository,
        application_repository: ApplicationRepository,
        user_repository: UserRepository
    ):
        self._processing_job_repository = processing_job_repository
        self._credential_repository = credential_repository
        self._application_repository = application_repository
        self._user_repository = user_repository

    async def create_processing_job(
        self,
        credential_id: UUID,
        user_id: UUID,
        application_id: UUID,
        priority: JobPriority = JobPriority.NORMAL,
        ai_provider: Optional[AIProvider] = None,
        processing_config: Optional[Dict[str, Any]] = None
    ) -> ProcessingJob:
        """Create a new processing job.
        
        Args:
            credential_id: Credential's unique identifier
            user_id: User's unique identifier
            application_id: Application's unique identifier
            priority: Job priority
            ai_provider: Preferred AI provider
            processing_config: Optional processing configuration
            
        Returns:
            The created processing job
            
        Raises:
            ValidationException: If validation fails
            BusinessLogicError: If business rules are violated
            NotFoundError: If entities not found
            AuthorizationException: If user doesn't have access
        """
        # Validate entities exist and user has access
        await self._validate_job_creation(
            credential_id, user_id, application_id
        )
        
        # Check processing limits
        await self._check_processing_limits(user_id, application_id)
        
        # Determine AI provider
        if not ai_provider:
            ai_provider = await self._select_optimal_ai_provider(user_id)
        
        # Create processing job
        job = ProcessingJob.create(
            credential_id=credential_id,
            user_id=user_id,
            application_id=application_id,
            priority=priority,
            ai_provider=ai_provider,
            processing_config=processing_config or {}
        )
        
        # Update credential status
        credential = await self._credential_repository.get_by_id(credential_id)
        credential.start_processing()
        await self._credential_repository.update(credential)
        
        return await self._processing_job_repository.create(job)

    async def start_job_processing(
        self,
        job_id: UUID,
        worker_id: str
    ) -> ProcessingJob:
        """Start processing a job.
        
        Args:
            job_id: Job's unique identifier
            worker_id: Worker identifier
            
        Returns:
            The started job
            
        Raises:
            NotFoundError: If job not found
            BusinessLogicError: If job cannot be started
        """
        job = await self._processing_job_repository.get_by_id(job_id)
        if not job:
            raise NotFoundError("Processing job not found")
        
        if job.status != JobStatus.QUEUED:
            raise BusinessLogicError(f"Job cannot be started from status: {job.status}")
        
        # Start the job
        job.start_processing(worker_id)
        
        return await self._processing_job_repository.update(job)

    async def update_job_stage(
        self,
        job_id: UUID,
        stage: ProcessingStage,
        progress: Optional[float] = None,
        stage_data: Optional[Dict[str, Any]] = None
    ) -> ProcessingJob:
        """Update job processing stage.
        
        Args:
            job_id: Job's unique identifier
            stage: New processing stage
            progress: Optional progress percentage
            stage_data: Optional stage-specific data
            
        Returns:
            The updated job
            
        Raises:
            NotFoundError: If job not found
            BusinessLogicError: If stage transition is invalid
        """
        job = await self._processing_job_repository.get_by_id(job_id)
        if not job:
            raise NotFoundError("Processing job not found")
        
        if job.status != JobStatus.PROCESSING:
            raise BusinessLogicError(f"Cannot update stage for job with status: {job.status}")
        
        # Update stage
        job.update_stage(stage, progress, stage_data)
        
        return await self._processing_job_repository.update(job)

    async def complete_job(
        self,
        job_id: UUID,
        result_data: Dict[str, Any],
        extracted_data: Dict[str, Any],
        quality_score: float
    ) -> ProcessingJob:
        """Complete a processing job successfully.
        
        Args:
            job_id: Job's unique identifier
            result_data: Processing result data
            extracted_data: Extracted credential data
            quality_score: Quality score of extraction
            
        Returns:
            The completed job
            
        Raises:
            NotFoundError: If job not found
            BusinessLogicError: If job cannot be completed
            ValidationException: If result data is invalid
        """
        job = await self._processing_job_repository.get_by_id(job_id)
        if not job:
            raise NotFoundError("Processing job not found")
        
        if job.status != JobStatus.PROCESSING:
            raise BusinessLogicError(f"Cannot complete job with status: {job.status}")
        
        # Validate result data
        self._validate_result_data(result_data, extracted_data, quality_score)
        
        # Complete the job
        job.complete_processing(result_data, extracted_data, quality_score)
        
        # Update credential with extracted data
        credential = await self._credential_repository.get_by_id(job.credential_id)
        credential.complete_processing(extracted_data, quality_score)
        await self._credential_repository.update(credential)
        
        return await self._processing_job_repository.update(job)

    async def fail_job(
        self,
        job_id: UUID,
        error_message: str,
        error_code: str,
        error_details: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> ProcessingJob:
        """Fail a processing job.
        
        Args:
            job_id: Job's unique identifier
            error_message: Error message
            error_code: Error code
            error_details: Optional error details
            retry: Whether to retry the job
            
        Returns:
            The failed job
            
        Raises:
            NotFoundError: If job not found
            BusinessLogicError: If job cannot be failed
        """
        job = await self._processing_job_repository.get_by_id(job_id)
        if not job:
            raise NotFoundError("Processing job not found")
        
        if job.status not in [JobStatus.PROCESSING, JobStatus.QUEUED]:
            raise BusinessLogicError(f"Cannot fail job with status: {job.status}")
        
        # Add error to job
        job.add_error(error_message, error_code, error_details)
        
        # Determine if we should retry
        should_retry = (
            retry and 
            job.retry_count < self.MAX_RETRY_ATTEMPTS and
            self._is_retryable_error(error_code)
        )
        
        if should_retry:
            # Retry with different AI provider if possible
            new_provider = self._get_next_ai_provider(job.ai_provider)
            job.retry_processing(new_provider)
        else:
            # Fail permanently
            job.fail_processing(error_message, error_code, error_details)
            
            # Update credential status
            credential = await self._credential_repository.get_by_id(job.credential_id)
            credential.fail_processing(error_message)
            await self._credential_repository.update(credential)
        
        return await self._processing_job_repository.update(job)

    async def cancel_job(
        self,
        job_id: UUID,
        user_id: UUID,
        reason: str = "User requested cancellation"
    ) -> ProcessingJob:
        """Cancel a processing job.
        
        Args:
            job_id: Job's unique identifier
            user_id: User's unique identifier
            reason: Cancellation reason
            
        Returns:
            The cancelled job
            
        Raises:
            NotFoundError: If job not found
            AuthorizationException: If user doesn't own the job
            BusinessLogicError: If job cannot be cancelled
        """
        job = await self._processing_job_repository.get_by_id(job_id)
        if not job:
            raise NotFoundError("Processing job not found")
        
        if job.user_id != user_id:
            raise AuthorizationException("User does not own this job")
        
        if job.status not in [JobStatus.QUEUED, JobStatus.PROCESSING]:
            raise BusinessLogicError(f"Cannot cancel job with status: {job.status}")
        
        # Cancel the job
        job.cancel_processing(reason)
        
        # Update credential status
        credential = await self._credential_repository.get_by_id(job.credential_id)
        credential.cancel_processing()
        await self._credential_repository.update(credential)
        
        return await self._processing_job_repository.update(job)

    async def timeout_stalled_jobs(self) -> List[ProcessingJob]:
        """Timeout jobs that have been stalled for too long.
        
        Returns:
            List of timed out jobs
        """
        timed_out_jobs = []
        
        # Get stalled jobs
        stalled_jobs = await self._processing_job_repository.get_stalled_jobs(
            minutes=self.JOB_TIMEOUT_MINUTES
        )
        
        for job in stalled_jobs:
            try:
                # Check if job has exceeded stage timeout
                stage_timeout = self.STAGE_TIMEOUTS.get(job.current_stage, self.JOB_TIMEOUT_MINUTES)
                stage_duration = (datetime.utcnow() - job.stage_updated_at).total_seconds() / 60
                
                if stage_duration > stage_timeout:
                    job.timeout_processing(f"Job timed out in stage {job.current_stage}")
                    
                    # Update credential status
                    credential = await self._credential_repository.get_by_id(job.credential_id)
                    credential.fail_processing("Processing timed out")
                    await self._credential_repository.update(credential)
                    
                    await self._processing_job_repository.update(job)
                    timed_out_jobs.append(job)
                    
            except Exception as e:
                # Log error but continue with other jobs
                job.add_log(f"Error during timeout check: {str(e)}")
                await self._processing_job_repository.update(job)
        
        return timed_out_jobs

    async def get_next_job_in_queue(
        self,
        worker_capabilities: Optional[List[str]] = None
    ) -> Optional[ProcessingJob]:
        """Get the next job in the processing queue.
        
        Args:
            worker_capabilities: Optional list of worker capabilities
            
        Returns:
            Next job to process or None if queue is empty
        """
        return await self._processing_job_repository.get_next_in_queue()

    async def get_job_statistics(
        self,
        user_id: Optional[UUID] = None,
        application_id: Optional[UUID] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get processing job statistics.
        
        Args:
            user_id: Optional user filter
            application_id: Optional application filter
            date_range: Optional date range filter
            
        Returns:
            Dictionary containing job statistics
        """
        stats = await self._processing_job_repository.get_queue_stats()
        
        # Add additional statistics
        if date_range:
            start_date, end_date = date_range
            jobs_in_range = await self._processing_job_repository.get_by_date_range(
                start_date, end_date, user_id, application_id
            )
            
            stats['date_range_stats'] = {
                'total_jobs': len(jobs_in_range),
                'completed_jobs': len([j for j in jobs_in_range if j.status == JobStatus.COMPLETED]),
                'failed_jobs': len([j for j in jobs_in_range if j.status == JobStatus.FAILED]),
                'cancelled_jobs': len([j for j in jobs_in_range if j.status == JobStatus.CANCELLED]),
                'average_processing_time': self._calculate_average_processing_time(jobs_in_range)
            }
        
        return stats

    async def _validate_job_creation(
        self,
        credential_id: UUID,
        user_id: UUID,
        application_id: UUID
    ) -> None:
        """Validate entities for job creation.
        
        Args:
            credential_id: Credential's unique identifier
            user_id: User's unique identifier
            application_id: Application's unique identifier
            
        Raises:
            NotFoundError: If entities not found
            AuthorizationException: If user doesn't have access
            BusinessLogicError: If entities are in invalid state
        """
        # Check credential exists and belongs to user
        credential = await self._credential_repository.get_by_id(credential_id)
        if not credential:
            raise NotFoundError("Credential not found")
        
        if credential.user_id != user_id:
            raise AuthorizationException("User does not own this credential")
        
        if credential.processing_status != ProcessingStatus.PENDING:
            raise BusinessLogicError(
                f"Credential is not in pending status: {credential.processing_status}"
            )
        
        # Check application exists and belongs to user
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        if application.user_id != user_id:
            raise AuthorizationException("User does not own this application")
        
        if not application.is_active:
            raise BusinessLogicError("Application is not active")
        
        # Check user exists and is active
        user = await self._user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise NotFoundError("User not found or inactive")

    async def _check_processing_limits(
        self,
        user_id: UUID,
        application_id: UUID
    ) -> None:
        """Check processing limits for user and application.
        
        Args:
            user_id: User's unique identifier
            application_id: Application's unique identifier
            
        Raises:
            RateLimitError: If limits are exceeded
        """
        # Check concurrent processing jobs
        active_jobs = await self._processing_job_repository.get_by_status(
            JobStatus.PROCESSING, user_id=user_id
        )
        
        application = await self._application_repository.get_by_id(application_id)
        max_concurrent = application.limits.concurrent_requests
        
        if len(active_jobs) >= max_concurrent:
            raise RateLimitError(
                f"Maximum concurrent processing jobs reached ({max_concurrent})"
            )
        
        # Check daily processing limit
        today = datetime.utcnow().date()
        today_jobs = await self._processing_job_repository.get_by_date_range(
            datetime.combine(today, datetime.min.time()),
            datetime.combine(today, datetime.max.time()),
            user_id=user_id,
            application_id=application_id
        )
        
        daily_limit = application.limits.daily_requests
        if len(today_jobs) >= daily_limit:
            raise RateLimitError(f"Daily processing limit reached ({daily_limit})")

    async def _select_optimal_ai_provider(self, user_id: UUID) -> AIProvider:
        """Select optimal AI provider based on availability and user preferences.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Selected AI provider
        """
        # For now, return the first provider in fallback order
        # In a real implementation, this would check provider availability,
        # user preferences, costs, etc.
        return self.AI_PROVIDER_FALLBACK[0]

    def _get_next_ai_provider(self, current_provider: AIProvider) -> Optional[AIProvider]:
        """Get next AI provider for retry.
        
        Args:
            current_provider: Current AI provider
            
        Returns:
            Next AI provider or None if no alternatives
        """
        try:
            current_index = self.AI_PROVIDER_FALLBACK.index(current_provider)
            if current_index < len(self.AI_PROVIDER_FALLBACK) - 1:
                return self.AI_PROVIDER_FALLBACK[current_index + 1]
        except ValueError:
            pass
        
        return None

    def _is_retryable_error(self, error_code: str) -> bool:
        """Check if error is retryable.
        
        Args:
            error_code: Error code
            
        Returns:
            True if error is retryable
        """
        retryable_errors = {
            'TIMEOUT',
            'NETWORK_ERROR',
            'AI_PROVIDER_UNAVAILABLE',
            'RATE_LIMITED',
            'TEMPORARY_FAILURE'
        }
        
        return error_code in retryable_errors

    def _validate_result_data(
        self,
        result_data: Dict[str, Any],
        extracted_data: Dict[str, Any],
        quality_score: float
    ) -> None:
        """Validate processing result data.
        
        Args:
            result_data: Processing result data
            extracted_data: Extracted credential data
            quality_score: Quality score
            
        Raises:
            ValidationException: If validation fails
        """
        if not isinstance(result_data, dict):
            raise ValidationException("Result data must be a dictionary")
        
        if not isinstance(extracted_data, dict):
            raise ValidationException("Extracted data must be a dictionary")
        
        if not isinstance(quality_score, (int, float)) or not (0 <= quality_score <= 1):
            raise ValidationException("Quality score must be a number between 0 and 1")
        
        # Check required fields in extracted data
        required_fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'curp']
        for field in required_fields:
            if field not in extracted_data or not extracted_data[field]:
                raise ValidationException(f"Missing required field in extracted data: {field}")

    def _calculate_average_processing_time(self, jobs: List[ProcessingJob]) -> Optional[float]:
        """Calculate average processing time for completed jobs.
        
        Args:
            jobs: List of processing jobs
            
        Returns:
            Average processing time in seconds or None
        """
        completed_jobs = [
            job for job in jobs 
            if job.status == JobStatus.COMPLETED and job.completed_at and job.started_at
        ]
        
        if not completed_jobs:
            return None
        
        total_time = sum(
            (job.completed_at - job.started_at).total_seconds()
            for job in completed_jobs
        )
        
        return total_time / len(completed_jobs)