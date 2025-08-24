#!/usr/bin/env python3
"""
Processing Job Database Model

SQLAlchemy model for credential processing job data persistence.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship

from ..base import BaseModel
from ....domain.entities.processing_job import (
    JobStatus, JobPriority, ProcessingStage, AIProvider
)


class ProcessingJobModel(BaseModel):
    """Processing job database model."""
    
    __tablename__ = "processing_jobs"
    
    # Foreign keys
    credential_id = Column(
        String(36),
        ForeignKey("credentials.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    application_id = Column(
        String(36),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Job information
    status = Column(
        SQLEnum(JobStatus),
        nullable=False,
        default=JobStatus.PENDING,
        index=True
    )
    
    priority = Column(
        SQLEnum(JobPriority),
        nullable=False,
        default=JobPriority.NORMAL,
        index=True
    )
    
    current_stage = Column(
        SQLEnum(ProcessingStage),
        nullable=False,
        default=ProcessingStage.VALIDATION,
        index=True
    )
    
    ai_provider = Column(
        SQLEnum(AIProvider),
        nullable=True,
        index=True
    )
    
    # Processing configuration (stored as JSON)
    config = Column(
        JSON,
        nullable=False,
        default=dict
    )
    
    # Timing information
    started_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    completed_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    failed_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    timeout_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    stage_started_at = Column(
        DateTime,
        nullable=True
    )
    
    stage_timeout_at = Column(
        DateTime,
        nullable=True
    )
    
    # Processing metrics (stored as JSON)
    metrics = Column(
        JSON,
        nullable=False,
        default=dict
    )
    
    # Processing result (stored as JSON)
    result = Column(
        JSON,
        nullable=True
    )
    
    # Error information
    errors = Column(
        JSON,
        nullable=False,
        default=list
    )
    
    # Processing logs (stored as JSON array)
    logs = Column(
        JSON,
        nullable=False,
        default=list
    )
    
    # Retry information
    retry_count = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    max_retries = Column(
        Integer,
        nullable=False,
        default=3
    )
    
    last_retry_at = Column(
        DateTime,
        nullable=True
    )
    
    # Progress tracking
    progress_percentage = Column(
        Float,
        nullable=False,
        default=0.0
    )
    
    estimated_completion_at = Column(
        DateTime,
        nullable=True
    )
    
    # Cost tracking
    estimated_cost = Column(
        Float,
        nullable=False,
        default=0.0
    )
    
    actual_cost = Column(
        Float,
        nullable=True
    )
    
    # Processing time in seconds
    processing_time_seconds = Column(
        Float,
        nullable=True
    )
    
    # Worker information
    worker_id = Column(
        String(100),
        nullable=True,
        index=True
    )
    
    worker_node = Column(
        String(100),
        nullable=True
    )
    
    # Soft delete
    deleted_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    # Additional metadata
    extra_metadata = Column(
        JSON,
        nullable=False,
        default=dict
    )
    
    # Relationships
    credential = relationship(
        "CredentialModel",
        back_populates="processing_jobs"
    )
    
    user = relationship(
        "UserModel",
        back_populates="processing_jobs"
    )
    
    application = relationship(
        "ApplicationModel",
        back_populates="processing_jobs"
    )
    
    def to_domain_entity(self):
        """Convert database model to domain entity.
        
        Returns:
            ProcessingJob domain entity
        """
        from ....domain.entities.processing_job import (
            ProcessingJob, ProcessingConfig, ProcessingMetrics,
            ProcessingError, ProcessingResult
        )
        
        # Convert config
        config_data = self.config or {}
        config = ProcessingConfig(
            use_ocr=config_data.get('use_ocr', True),
            use_qr=config_data.get('use_qr', True),
            use_ai=config_data.get('use_ai', True),
            ai_provider=AIProvider(config_data['ai_provider']) if config_data.get('ai_provider') else None,
            ai_model=config_data.get('ai_model'),
            ocr_language=config_data.get('ocr_language', 'spa'),
            quality_threshold=config_data.get('quality_threshold', 0.8),
            timeout_seconds=config_data.get('timeout_seconds', 300),
            retry_on_failure=config_data.get('retry_on_failure', True),
            save_intermediate_results=config_data.get('save_intermediate_results', False),
            custom_prompts=config_data.get('custom_prompts', {}),
            processing_options=config_data.get('processing_options', {})
        )
        
        # Convert metrics
        metrics_data = self.metrics or {}
        metrics = ProcessingMetrics(
            total_duration=metrics_data.get('total_duration', 0.0),
            ocr_duration=metrics_data.get('ocr_duration', 0.0),
            qr_duration=metrics_data.get('qr_duration', 0.0),
            ai_duration=metrics_data.get('ai_duration', 0.0),
            validation_duration=metrics_data.get('validation_duration', 0.0),
            queue_wait_time=metrics_data.get('queue_wait_time', 0.0),
            memory_usage_mb=metrics_data.get('memory_usage_mb', 0.0),
            cpu_usage_percent=metrics_data.get('cpu_usage_percent', 0.0),
            api_calls_made=metrics_data.get('api_calls_made', 0),
            tokens_used=metrics_data.get('tokens_used', 0),
            cost_breakdown=metrics_data.get('cost_breakdown', {})
        )
        
        # Convert errors
        errors_list = []
        for error_data in self.errors or []:
            error = ProcessingError(
                stage=ProcessingStage(error_data['stage']),
                error_type=error_data['error_type'],
                message=error_data['message'],
                details=error_data.get('details', {}),
                timestamp=datetime.fromisoformat(error_data['timestamp']),
                is_recoverable=error_data.get('is_recoverable', False)
            )
            errors_list.append(error)
        
        # Convert result
        result = None
        if self.result:
            result_data = self.result
            result = ProcessingResult(
                extracted_data=result_data.get('extracted_data', {}),
                confidence_scores=result_data.get('confidence_scores', {}),
                validation_results=result_data.get('validation_results', {}),
                quality_metrics=result_data.get('quality_metrics', {}),
                processing_notes=result_data.get('processing_notes', []),
                intermediate_results=result_data.get('intermediate_results', {})
            )
        
        return ProcessingJob(
            id=self.id,
            credential_id=self.credential_id,
            user_id=self.user_id,
            application_id=self.application_id,
            status=self.status,
            priority=self.priority,
            current_stage=self.current_stage,
            ai_provider=self.ai_provider,
            config=config,
            started_at=self.started_at,
            completed_at=self.completed_at,
            failed_at=self.failed_at,
            timeout_at=self.timeout_at,
            stage_started_at=self.stage_started_at,
            stage_timeout_at=self.stage_timeout_at,
            metrics=metrics,
            result=result,
            errors=errors_list,
            logs=self.logs or [],
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            last_retry_at=self.last_retry_at,
            progress_percentage=self.progress_percentage,
            estimated_completion_at=self.estimated_completion_at,
            estimated_cost=self.estimated_cost,
            actual_cost=self.actual_cost,
            worker_id=self.worker_id,
            worker_node=self.worker_node,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            metadata=self.extra_metadata or {}
        )
    
    @classmethod
    def from_domain_entity(cls, job):
        """Create database model from domain entity.
        
        Args:
            job: ProcessingJob domain entity
            
        Returns:
            ProcessingJobModel instance
        """
        # Convert config to dict
        config_dict = {
            'use_ocr': job.config.use_ocr,
            'use_qr': job.config.use_qr,
            'use_ai': job.config.use_ai,
            'ai_provider': job.config.ai_provider.value if job.config.ai_provider else None,
            'ai_model': job.config.ai_model,
            'ocr_language': job.config.ocr_language,
            'quality_threshold': job.config.quality_threshold,
            'timeout_seconds': job.config.timeout_seconds,
            'retry_on_failure': job.config.retry_on_failure,
            'save_intermediate_results': job.config.save_intermediate_results,
            'custom_prompts': job.config.custom_prompts,
            'processing_options': job.config.processing_options
        }
        
        # Convert metrics to dict
        metrics_dict = {
            'total_duration': job.metrics.total_duration,
            'ocr_duration': job.metrics.ocr_duration,
            'qr_duration': job.metrics.qr_duration,
            'ai_duration': job.metrics.ai_duration,
            'validation_duration': job.metrics.validation_duration,
            'queue_wait_time': job.metrics.queue_wait_time,
            'memory_usage_mb': job.metrics.memory_usage_mb,
            'cpu_usage_percent': job.metrics.cpu_usage_percent,
            'api_calls_made': job.metrics.api_calls_made,
            'tokens_used': job.metrics.tokens_used,
            'cost_breakdown': job.metrics.cost_breakdown
        }
        
        # Convert errors to dict list
        errors_list = []
        for error in job.errors:
            error_dict = {
                'stage': error.stage.value,
                'error_type': error.error_type,
                'message': error.message,
                'details': error.details,
                'timestamp': error.timestamp.isoformat(),
                'is_recoverable': error.is_recoverable
            }
            errors_list.append(error_dict)
        
        # Convert result to dict
        result_dict = None
        if job.result:
            result_dict = {
                'extracted_data': job.result.extracted_data,
                'confidence_scores': job.result.confidence_scores,
                'validation_results': job.result.validation_results,
                'quality_metrics': job.result.quality_metrics,
                'processing_notes': job.result.processing_notes,
                'intermediate_results': job.result.intermediate_results
            }
        
        return cls(
            id=job.id,
            credential_id=job.credential_id,
            user_id=job.user_id,
            application_id=job.application_id,
            status=job.status,
            priority=job.priority,
            current_stage=job.current_stage,
            ai_provider=job.ai_provider,
            config=config_dict,
            started_at=job.started_at,
            completed_at=job.completed_at,
            failed_at=job.failed_at,
            timeout_at=job.timeout_at,
            stage_started_at=job.stage_started_at,
            stage_timeout_at=job.stage_timeout_at,
            metrics=metrics_dict,
            result=result_dict,
            errors=errors_list,
            logs=job.logs,
            retry_count=job.retry_count,
            max_retries=job.max_retries,
            last_retry_at=job.last_retry_at,
            progress_percentage=job.progress_percentage,
            estimated_completion_at=job.estimated_completion_at,
            estimated_cost=job.estimated_cost,
            actual_cost=job.actual_cost,
            worker_id=job.worker_id,
            worker_node=job.worker_node,
            created_at=job.created_at,
            updated_at=job.updated_at,
            deleted_at=job.deleted_at,
            extra_metadata=job.metadata
        )
    
    def update_from_domain_entity(self, job) -> None:
        """Update database model from domain entity.
        
        Args:
            job: ProcessingJob domain entity
        """
        # Update basic fields
        self.status = job.status
        self.priority = job.priority
        self.current_stage = job.current_stage
        self.ai_provider = job.ai_provider
        self.started_at = job.started_at
        self.completed_at = job.completed_at
        self.failed_at = job.failed_at
        self.timeout_at = job.timeout_at
        self.stage_started_at = job.stage_started_at
        self.stage_timeout_at = job.stage_timeout_at
        self.retry_count = job.retry_count
        self.max_retries = job.max_retries
        self.last_retry_at = job.last_retry_at
        self.progress_percentage = job.progress_percentage
        self.estimated_completion_at = job.estimated_completion_at
        self.estimated_cost = job.estimated_cost
        self.actual_cost = job.actual_cost
        self.worker_id = job.worker_id
        self.worker_node = job.worker_node
        self.deleted_at = job.deleted_at
        self.extra_metadata = job.metadata
        self.logs = job.logs
        
        # Update config
        self.config = {
            'use_ocr': job.config.use_ocr,
            'use_qr': job.config.use_qr,
            'use_ai': job.config.use_ai,
            'ai_provider': job.config.ai_provider.value if job.config.ai_provider else None,
            'ai_model': job.config.ai_model,
            'ocr_language': job.config.ocr_language,
            'quality_threshold': job.config.quality_threshold,
            'timeout_seconds': job.config.timeout_seconds,
            'retry_on_failure': job.config.retry_on_failure,
            'save_intermediate_results': job.config.save_intermediate_results,
            'custom_prompts': job.config.custom_prompts,
            'processing_options': job.config.processing_options
        }
        
        # Update metrics
        self.metrics = {
            'total_duration': job.metrics.total_duration,
            'ocr_duration': job.metrics.ocr_duration,
            'qr_duration': job.metrics.qr_duration,
            'ai_duration': job.metrics.ai_duration,
            'validation_duration': job.metrics.validation_duration,
            'queue_wait_time': job.metrics.queue_wait_time,
            'memory_usage_mb': job.metrics.memory_usage_mb,
            'cpu_usage_percent': job.metrics.cpu_usage_percent,
            'api_calls_made': job.metrics.api_calls_made,
            'tokens_used': job.metrics.tokens_used,
            'cost_breakdown': job.metrics.cost_breakdown
        }
        
        # Update errors
        errors_list = []
        for error in job.errors:
            error_dict = {
                'stage': error.stage.value,
                'error_type': error.error_type,
                'message': error.message,
                'details': error.details,
                'timestamp': error.timestamp.isoformat(),
                'is_recoverable': error.is_recoverable
            }
            errors_list.append(error_dict)
        self.errors = errors_list
        
        # Update result
        if job.result:
            self.result = {
                'extracted_data': job.result.extracted_data,
                'confidence_scores': job.result.confidence_scores,
                'validation_results': job.result.validation_results,
                'quality_metrics': job.result.quality_metrics,
                'processing_notes': job.result.processing_notes,
                'intermediate_results': job.result.intermediate_results
            }
        else:
            self.result = None
        
        # Update timestamps
        self.updated_at = job.updated_at or datetime.utcnow()
    
    @property
    def is_active(self) -> bool:
        """Check if job is currently active.
        
        Returns:
            True if job is active
        """
        return self.status in [
            JobStatus.PENDING,
            JobStatus.RUNNING,
            JobStatus.RETRYING
        ]
    
    @property
    def is_finished(self) -> bool:
        """Check if job is finished.
        
        Returns:
            True if job is finished
        """
        return self.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.TIMEOUT
        ]
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get job duration in seconds.
        
        Returns:
            Duration in seconds or None
        """
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        elif self.started_at:
            delta = datetime.utcnow() - self.started_at
            return delta.total_seconds()
        return None
    
    @property
    def can_retry(self) -> bool:
        """Check if job can be retried.
        
        Returns:
            True if job can be retried
        """
        return (
            self.status == JobStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    def __repr__(self) -> str:
        """String representation of the processing job model."""
        return f"<ProcessingJobModel(id={self.id}, status={self.status}, stage={self.current_stage})>"