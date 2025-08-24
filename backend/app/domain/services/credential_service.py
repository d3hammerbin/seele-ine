#!/usr/bin/env python3
"""
Credential Processing Domain Service

Contains business logic for credential processing operations.
Handles complex credential-related business rules and validations.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import mimetypes
from pathlib import Path

from ..entities.credential import (
    Credential, CredentialType, ProcessingStatus, ExtractionMethod, Gender
)
from ..entities.processing_job import ProcessingJob, JobStatus, JobPriority, ProcessingStage
from ..repositories.credential_repository import CredentialRepository
from ..repositories.processing_job_repository import ProcessingJobRepository
from ..repositories.user_repository import UserRepository
from ..repositories.application_repository import ApplicationRepository
from ...core.exceptions.base import (
    ValidationException, BusinessLogicError, NotFoundError,
    CredentialProcessingError, ImageValidationError
)


class CredentialService:
    """Domain service for credential processing business logic."""

    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Minimum image dimensions
    MIN_WIDTH = 300
    MIN_HEIGHT = 200

    def __init__(
        self,
        credential_repository: CredentialRepository,
        processing_job_repository: ProcessingJobRepository,
        user_repository: UserRepository,
        application_repository: ApplicationRepository
    ):
        self._credential_repository = credential_repository
        self._processing_job_repository = processing_job_repository
        self._user_repository = user_repository
        self._application_repository = application_repository

    async def submit_credential_for_processing(
        self,
        user_id: UUID,
        application_id: UUID,
        image_path: str,
        credential_type: CredentialType,
        priority: JobPriority = JobPriority.NORMAL,
        extraction_method: ExtractionMethod = ExtractionMethod.HYBRID
    ) -> Tuple[Credential, ProcessingJob]:
        """Submit a credential for processing.
        
        Args:
            user_id: User's unique identifier
            application_id: Application's unique identifier
            image_path: Path to the credential image
            credential_type: Type of credential
            priority: Processing priority
            extraction_method: Preferred extraction method
            
        Returns:
            Tuple of (credential, processing_job)
            
        Raises:
            ValidationException: If validation fails
            BusinessLogicError: If business rules are violated
            ImageValidationError: If image validation fails
        """
        # Validate user exists and is active
        user = await self._user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValidationException("Invalid or inactive user")
        
        # Validate application exists and is active
        application = await self._application_repository.get_by_id(application_id)
        if not application or not application.is_active:
            raise ValidationException("Invalid or inactive application")
        
        # Validate application belongs to user
        if application.user_id != user_id:
            raise ValidationException("Application does not belong to user")
        
        # Validate image file
        await self._validate_image_file(image_path)
        
        # Check user's processing limits
        await self._check_processing_limits(user_id, application_id)
        
        # Create credential entity
        credential = Credential.create(
            user_id=user_id,
            application_id=application_id,
            credential_type=credential_type,
            image_path=image_path,
            extraction_method=extraction_method
        )
        
        # Save credential
        credential = await self._credential_repository.create(credential)
        
        # Create processing job
        processing_job = ProcessingJob.create(
            credential_id=credential.id,
            user_id=user_id,
            application_id=application_id,
            priority=priority
        )
        
        # Save processing job
        processing_job = await self._processing_job_repository.create(processing_job)
        
        return credential, processing_job

    async def process_credential(
        self,
        credential_id: UUID,
        extracted_data: Dict[str, Any],
        confidence_scores: Dict[str, float],
        processing_time: float,
        ai_provider_used: str
    ) -> Credential:
        """Process a credential with extracted data.
        
        Args:
            credential_id: Credential's unique identifier
            extracted_data: Extracted data from the credential
            confidence_scores: Confidence scores for extracted fields
            processing_time: Time taken for processing
            ai_provider_used: AI provider used for processing
            
        Returns:
            The processed credential
            
        Raises:
            NotFoundError: If credential not found
            CredentialProcessingError: If processing fails
        """
        credential = await self._credential_repository.get_by_id(credential_id)
        if not credential:
            raise NotFoundError("Credential not found")
        
        if credential.status != ProcessingStatus.PROCESSING:
            raise CredentialProcessingError(
                f"Credential is not in processing status: {credential.status}"
            )
        
        try:
            # Validate extracted data
            self._validate_extracted_data(extracted_data, credential.credential_type)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(confidence_scores, extracted_data)
            
            # Update credential with processed data
            credential.complete_processing(
                extracted_data=extracted_data,
                confidence_scores=confidence_scores,
                processing_time=processing_time,
                ai_provider_used=ai_provider_used,
                quality_score=quality_score
            )
            
            # Save updated credential
            credential = await self._credential_repository.update(credential)
            
            # Update processing job status
            job = await self._processing_job_repository.get_by_credential_id(credential_id)
            if job:
                job.complete({
                    'credential_id': credential_id,
                    'quality_score': quality_score,
                    'processing_time': processing_time
                })
                await self._processing_job_repository.update(job)
            
            return credential
            
        except Exception as e:
            # Mark credential as failed
            credential.fail_processing(str(e))
            await self._credential_repository.update(credential)
            
            # Update processing job status
            job = await self._processing_job_repository.get_by_credential_id(credential_id)
            if job:
                job.fail(str(e))
                await self._processing_job_repository.update(job)
            
            raise CredentialProcessingError(f"Processing failed: {str(e)}")

    async def retry_failed_credential(
        self,
        credential_id: UUID,
        new_extraction_method: Optional[ExtractionMethod] = None
    ) -> ProcessingJob:
        """Retry processing a failed credential.
        
        Args:
            credential_id: Credential's unique identifier
            new_extraction_method: Optional new extraction method to try
            
        Returns:
            New processing job for the retry
            
        Raises:
            NotFoundError: If credential not found
            BusinessLogicError: If retry is not allowed
        """
        credential = await self._credential_repository.get_by_id(credential_id)
        if not credential:
            raise NotFoundError("Credential not found")
        
        if credential.status != ProcessingStatus.FAILED:
            raise BusinessLogicError("Only failed credentials can be retried")
        
        if credential.retry_count >= 3:
            raise BusinessLogicError("Maximum retry attempts exceeded")
        
        # Update extraction method if provided
        if new_extraction_method:
            credential.extraction_method = new_extraction_method
        
        # Reset credential for retry
        credential.retry_processing()
        await self._credential_repository.update(credential)
        
        # Create new processing job
        processing_job = ProcessingJob.create(
            credential_id=credential.id,
            user_id=credential.user_id,
            application_id=credential.application_id,
            priority=JobPriority.HIGH  # Higher priority for retries
        )
        
        return await self._processing_job_repository.create(processing_job)

    async def cancel_processing(
        self,
        credential_id: UUID,
        reason: str = "User requested cancellation"
    ) -> Credential:
        """Cancel credential processing.
        
        Args:
            credential_id: Credential's unique identifier
            reason: Reason for cancellation
            
        Returns:
            The cancelled credential
            
        Raises:
            NotFoundError: If credential not found
            BusinessLogicError: If cancellation is not allowed
        """
        credential = await self._credential_repository.get_by_id(credential_id)
        if not credential:
            raise NotFoundError("Credential not found")
        
        if credential.status not in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]:
            raise BusinessLogicError(f"Cannot cancel credential in {credential.status} status")
        
        # Cancel credential
        credential.cancel_processing(reason)
        credential = await self._credential_repository.update(credential)
        
        # Cancel processing job
        job = await self._processing_job_repository.get_by_credential_id(credential_id)
        if job and job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            job.cancel(reason)
            await self._processing_job_repository.update(job)
        
        return credential

    async def get_processing_statistics(
        self,
        user_id: Optional[UUID] = None,
        application_id: Optional[UUID] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get processing statistics.
        
        Args:
            user_id: Optional user ID to filter by
            application_id: Optional application ID to filter by
            date_range: Optional date range tuple (start, end)
            
        Returns:
            Dictionary containing processing statistics
        """
        filters = {}
        if user_id:
            filters['user_id'] = user_id
        if application_id:
            filters['application_id'] = application_id
        if date_range:
            filters['created_at__gte'] = date_range[0]
            filters['created_at__lte'] = date_range[1]
        
        # Get credential statistics
        credential_stats = await self._credential_repository.get_processing_stats(user_id)
        
        # Get job queue statistics
        job_stats = await self._processing_job_repository.get_queue_stats()
        
        return {
            'credentials': credential_stats,
            'jobs': job_stats,
            'filters_applied': filters
        }

    async def _validate_image_file(self, image_path: str) -> None:
        """Validate image file.
        
        Args:
            image_path: Path to the image file
            
        Raises:
            ImageValidationError: If image validation fails
        """
        path = Path(image_path)
        
        # Check if file exists
        if not path.exists():
            raise ImageValidationError("Image file does not exist")
        
        # Check file extension
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ImageValidationError(
                f"Unsupported image format. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ImageValidationError(
                f"Image file too large. Maximum size: {self.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type or not mime_type.startswith('image/'):
            raise ImageValidationError("File is not a valid image")

    async def _check_processing_limits(
        self,
        user_id: UUID,
        application_id: UUID
    ) -> None:
        """Check if user/application has exceeded processing limits.
        
        Args:
            user_id: User's unique identifier
            application_id: Application's unique identifier
            
        Raises:
            BusinessLogicError: If limits are exceeded
        """
        # Get user's current month processing count
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        user_credentials = await self._credential_repository.get_credentials_by_date_range(
            start_date=month_start,
            end_date=month_end,
            user_id=user_id
        )
        
        # Get user and application to check limits
        user = await self._user_repository.get_by_id(user_id)
        application = await self._application_repository.get_by_id(application_id)
        
        # Check user monthly limit based on subscription
        monthly_limits = {
            'FREE': 10,
            'BASIC': 100,
            'PREMIUM': 1000,
            'ENTERPRISE': 10000
        }
        
        user_limit = monthly_limits.get(user.subscription_plan.value, 10)
        if len(user_credentials) >= user_limit:
            raise BusinessLogicError(
                f"Monthly processing limit exceeded ({user_limit} for {user.subscription_plan.value} plan)"
            )
        
        # Check application daily limit
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1) - timedelta(seconds=1)
        
        app_credentials = await self._credential_repository.get_credentials_by_date_range(
            start_date=day_start,
            end_date=day_end,
            user_id=user_id
        )
        
        app_credentials_today = [
            c for c in app_credentials if c.application_id == application_id
        ]
        
        if len(app_credentials_today) >= application.limits.daily_requests:
            raise BusinessLogicError(
                f"Application daily limit exceeded ({application.limits.daily_requests})"
            )

    def _validate_extracted_data(
        self,
        extracted_data: Dict[str, Any],
        credential_type: CredentialType
    ) -> None:
        """Validate extracted data based on credential type.
        
        Args:
            extracted_data: Extracted data to validate
            credential_type: Type of credential
            
        Raises:
            ValidationException: If validation fails
        """
        if credential_type in [CredentialType.TIPO1, CredentialType.TIPO2, CredentialType.TIPO3]:
            required_fields = {
                'nombre', 'apellido_paterno', 'apellido_materno',
                'fecha_nacimiento', 'sexo', 'clave_elector'
            }
            
            missing_fields = required_fields - set(extracted_data.keys())
            if missing_fields:
                raise ValidationException(
                    f"Missing required fields for INE: {', '.join(missing_fields)}"
                )
            
            # Validate specific field formats
            if 'sexo' in extracted_data:
                if extracted_data['sexo'].upper() not in ['M', 'F', 'H', 'MASCULINO', 'FEMENINO']:
                    raise ValidationException("Invalid gender value")
            
            if 'clave_elector' in extracted_data:
                clave = extracted_data['clave_elector']
                if not isinstance(clave, str) or len(clave) != 18:
                    raise ValidationException("Invalid clave elector format")

    def _calculate_quality_score(
        self,
        confidence_scores: Dict[str, float],
        extracted_data: Dict[str, Any]
    ) -> float:
        """Calculate quality score based on confidence scores and data completeness.
        
        Args:
            confidence_scores: Confidence scores for each field
            extracted_data: Extracted data
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not confidence_scores:
            return 0.5  # Default score if no confidence data
        
        # Calculate average confidence
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
        
        # Calculate completeness score
        total_possible_fields = 10  # Adjust based on credential type
        completeness = len(extracted_data) / total_possible_fields
        
        # Weighted combination
        quality_score = (avg_confidence * 0.7) + (completeness * 0.3)
        
        return min(1.0, max(0.0, quality_score))