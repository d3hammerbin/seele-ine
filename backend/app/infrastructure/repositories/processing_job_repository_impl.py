#!/usr/bin/env python3
"""
Processing Job Repository Implementation

SQLAlchemy implementation of the ProcessingJobRepository interface.
Handles database operations for processing job entities.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.repositories.processing_job_repository import ProcessingJobRepository
from ...domain.entities.processing_job import ProcessingJob, JobStatus, JobPriority, ProcessingStage, AIProvider
from ...core.exceptions.base import RepositoryError, NotFoundError
from ..database.models.processing_job import ProcessingJobModel


class ProcessingJobRepositoryImpl(ProcessingJobRepository):
    """
    SQLAlchemy implementation of ProcessingJobRepository.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, job: ProcessingJob) -> ProcessingJob:
        """Create a new processing job in the database."""
        try:
            # Convert domain entity to database model
            job_model = ProcessingJobModel.from_domain_entity(job)
            
            # Add to session and commit
            self._session.add(job_model)
            await self._session.commit()
            await self._session.refresh(job_model)
            
            # Convert back to domain entity
            return job_model.to_domain_entity()
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to create processing job: {str(e)}")
    
    async def get_by_id(self, job_id: UUID) -> Optional[ProcessingJob]:
        """Get processing job by ID."""
        try:
            stmt = select(ProcessingJobModel).where(ProcessingJobModel.id == job_id)
            result = await self._session.execute(stmt)
            job_model = result.scalar_one_or_none()
            
            if job_model:
                return job_model.to_domain_entity()
            return None
            
        except Exception as e:
            raise RepositoryError(f"Failed to get processing job: {str(e)}")
    
    async def get_by_user_id(self, user_id: UUID, limit: int = 10, offset: int = 0) -> List[ProcessingJob]:
        """Get processing jobs by user ID."""
        try:
            stmt = (
                select(ProcessingJobModel)
                .where(ProcessingJobModel.user_id == user_id)
                .order_by(ProcessingJobModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get processing jobs by user: {str(e)}")
    
    async def get_by_application_id(self, application_id: UUID, limit: int = 10, offset: int = 0) -> List[ProcessingJob]:
        """Get processing jobs by application ID."""
        try:
            stmt = (
                select(ProcessingJobModel)
                .where(ProcessingJobModel.application_id == application_id)
                .order_by(ProcessingJobModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get processing jobs by application: {str(e)}")
    
    async def get_by_status(self, status: JobStatus, limit: int = 10, offset: int = 0) -> List[ProcessingJob]:
        """Get processing jobs by status."""
        try:
            stmt = (
                select(ProcessingJobModel)
                .where(ProcessingJobModel.status == status)
                .order_by(ProcessingJobModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get processing jobs by status: {str(e)}")
    
    async def get_by_period(self, start_date: datetime, end_date: datetime, user_id: Optional[UUID] = None, application_id: Optional[UUID] = None) -> List[ProcessingJob]:
        """Get processing jobs by date period."""
        try:
            conditions = [
                ProcessingJobModel.created_at >= start_date,
                ProcessingJobModel.created_at <= end_date
            ]
            
            if user_id:
                conditions.append(ProcessingJobModel.user_id == user_id)
            
            if application_id:
                conditions.append(ProcessingJobModel.application_id == application_id)
            
            stmt = (
                select(ProcessingJobModel)
                .where(and_(*conditions))
                .order_by(ProcessingJobModel.created_at.desc())
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get processing jobs by period: {str(e)}")
    
    async def update(self, job: ProcessingJob) -> ProcessingJob:
        """Update processing job."""
        try:
            # Get existing model
            stmt = select(ProcessingJobModel).where(ProcessingJobModel.id == job.id)
            result = await self._session.execute(stmt)
            job_model = result.scalar_one_or_none()
            
            if not job_model:
                raise NotFoundError(f"Processing job not found: {job.id}")
            
            # Update model from domain entity
            job_model.update_from_domain_entity(job)
            
            # Commit changes
            await self._session.commit()
            await self._session.refresh(job_model)
            
            return job_model.to_domain_entity()
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to update processing job: {str(e)}")
    
    async def delete(self, job_id: UUID) -> bool:
        """Delete processing job."""
        try:
            stmt = delete(ProcessingJobModel).where(ProcessingJobModel.id == job_id)
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to delete processing job: {str(e)}")
    
    async def get_pending_jobs(self, limit: int = 10) -> List[ProcessingJob]:
        """Get pending processing jobs."""
        try:
            stmt = (
                select(ProcessingJobModel)
                .where(ProcessingJobModel.status == JobStatus.PENDING)
                .order_by(ProcessingJobModel.priority.desc(), ProcessingJobModel.created_at.asc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get pending jobs: {str(e)}")
    
    async def get_active_jobs(self, user_id: Optional[UUID] = None) -> List[ProcessingJob]:
        """Get active processing jobs."""
        try:
            conditions = [
                ProcessingJobModel.status.in_([JobStatus.PENDING, JobStatus.PROCESSING, JobStatus.QUEUED])
            ]
            
            if user_id:
                conditions.append(ProcessingJobModel.user_id == user_id)
            
            stmt = (
                select(ProcessingJobModel)
                .where(and_(*conditions))
                .order_by(ProcessingJobModel.created_at.desc())
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get active jobs: {str(e)}")
    
    async def get_job_statistics(self, user_id: Optional[UUID] = None, application_id: Optional[UUID] = None, period_start: Optional[datetime] = None, period_end: Optional[datetime] = None) -> Dict[str, Any]:
        """Get processing job statistics."""
        try:
            conditions = []
            
            if user_id:
                conditions.append(ProcessingJobModel.user_id == user_id)
            
            if application_id:
                conditions.append(ProcessingJobModel.application_id == application_id)
            
            if period_start:
                conditions.append(ProcessingJobModel.created_at >= period_start)
            
            if period_end:
                conditions.append(ProcessingJobModel.created_at <= period_end)
            
            base_query = select(ProcessingJobModel)
            if conditions:
                base_query = base_query.where(and_(*conditions))
            
            # Total jobs
            count_stmt = select(func.count(ProcessingJobModel.id)).select_from(base_query.subquery())
            count_result = await self._session.execute(count_stmt)
            total_jobs = count_result.scalar()
            
            # Status statistics
            status_stmt = select(
                ProcessingJobModel.status,
                func.count(ProcessingJobModel.id).label('count')
            ).select_from(base_query.subquery()).group_by(ProcessingJobModel.status)
            
            status_result = await self._session.execute(status_stmt)
            status_stats = {row.status.value: row.count for row in status_result}
            
            # Processing time statistics
            time_stmt = select(
                func.avg(ProcessingJobModel.processing_time_seconds).label('avg_time'),
                func.min(ProcessingJobModel.processing_time_seconds).label('min_time'),
                func.max(ProcessingJobModel.processing_time_seconds).label('max_time'),
                func.sum(ProcessingJobModel.processing_time_seconds).label('total_time')
            ).select_from(base_query.subquery()).where(
                ProcessingJobModel.processing_time_seconds.isnot(None)
            )
            
            time_result = await self._session.execute(time_stmt)
            time_stats = time_result.first()
            
            # AI Provider statistics
            provider_stmt = select(
                ProcessingJobModel.ai_provider,
                func.count(ProcessingJobModel.id).label('count')
            ).select_from(base_query.subquery()).group_by(ProcessingJobModel.ai_provider)
            
            provider_result = await self._session.execute(provider_stmt)
            provider_stats = {row.ai_provider.value if row.ai_provider else 'unknown': row.count for row in provider_result}
            
            return {
                'total_jobs': total_jobs,
                'status_breakdown': status_stats,
                'processing_time': {
                    'average_seconds': float(time_stats.avg_time or 0),
                    'min_seconds': float(time_stats.min_time or 0),
                    'max_seconds': float(time_stats.max_time or 0),
                    'total_seconds': float(time_stats.total_time or 0)
                },
                'provider_breakdown': provider_stats,
                'success_rate': (status_stats.get('completed', 0) / total_jobs * 100) if total_jobs > 0 else 0,
                'failure_rate': (status_stats.get('failed', 0) / total_jobs * 100) if total_jobs > 0 else 0
            }
            
        except Exception as e:
            raise RepositoryError(f"Failed to get job statistics: {str(e)}")
    
    async def get_by_ai_provider(self, provider: AIProvider, limit: int = 50, offset: int = 0) -> List[ProcessingJob]:
        """Get processing jobs by AI provider."""
        try:
            stmt = (
                select(ProcessingJobModel)
                .where(ProcessingJobModel.ai_provider == provider)
                .order_by(ProcessingJobModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get jobs by AI provider: {str(e)}")
    
    async def get_failed_jobs(self, user_id: Optional[UUID] = None, limit: int = 10, offset: int = 0) -> List[ProcessingJob]:
        """Get failed processing jobs."""
        try:
            conditions = [ProcessingJobModel.status == JobStatus.FAILED]
            
            if user_id:
                conditions.append(ProcessingJobModel.user_id == user_id)
            
            stmt = (
                select(ProcessingJobModel)
                .where(and_(*conditions))
                .order_by(ProcessingJobModel.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get failed jobs: {str(e)}")

    async def get_by_credential_id(self, credential_id: UUID) -> Optional[ProcessingJob]:
        """Retrieve a processing job by credential ID."""
        try:
            stmt = select(ProcessingJobModel).where(ProcessingJobModel.credential_id == credential_id)
            result = await self._session.execute(stmt)
            job_model = result.scalar_one_or_none()
            
            if job_model:
                return job_model.to_domain_entity()
            return None
            
        except Exception as e:
            raise RepositoryError(f"Failed to get processing job by credential: {str(e)}")

    async def get_by_priority(self, priority: JobPriority, limit: int = 50, offset: int = 0) -> List[ProcessingJob]:
        """Retrieve processing jobs by priority."""
        try:
            stmt = (
                select(ProcessingJobModel)
                .where(ProcessingJobModel.priority == priority)
                .order_by(ProcessingJobModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get jobs by priority: {str(e)}")

    async def get_by_stage(self, stage: ProcessingStage, limit: int = 50, offset: int = 0) -> List[ProcessingJob]:
        """Retrieve processing jobs by current stage."""
        try:
            stmt = (
                select(ProcessingJobModel)
                .where(ProcessingJobModel.current_stage == stage)
                .order_by(ProcessingJobModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get jobs by stage: {str(e)}")

    async def list_jobs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[ProcessingJob]:
        """List processing jobs with optional filtering and sorting."""
        try:
            stmt = select(ProcessingJobModel)
            
            # Apply filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(ProcessingJobModel, key):
                        conditions.append(getattr(ProcessingJobModel, key) == value)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            # Apply sorting
            if hasattr(ProcessingJobModel, sort_by):
                sort_column = getattr(ProcessingJobModel, sort_by)
                if sort_order.lower() == "desc":
                    stmt = stmt.order_by(sort_column.desc())
                else:
                    stmt = stmt.order_by(sort_column.asc())
            
            stmt = stmt.limit(limit).offset(offset)
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to list jobs: {str(e)}")

    async def count_jobs(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count processing jobs with optional filtering."""
        try:
            stmt = select(func.count(ProcessingJobModel.id))
            
            # Apply filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(ProcessingJobModel, key):
                        conditions.append(getattr(ProcessingJobModel, key) == value)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            result = await self._session.execute(stmt)
            return result.scalar()
            
        except Exception as e:
            raise RepositoryError(f"Failed to count jobs: {str(e)}")

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get processing queue statistics."""
        try:
            # Status counts
            status_stmt = select(
                ProcessingJobModel.status,
                func.count(ProcessingJobModel.id).label('count')
            ).group_by(ProcessingJobModel.status)
            
            status_result = await self._session.execute(status_stmt)
            status_counts = {row.status.value: row.count for row in status_result}
            
            # Priority counts for pending jobs
            priority_stmt = select(
                ProcessingJobModel.priority,
                func.count(ProcessingJobModel.id).label('count')
            ).where(
                ProcessingJobModel.status == JobStatus.PENDING
            ).group_by(ProcessingJobModel.priority)
            
            priority_result = await self._session.execute(priority_stmt)
            priority_counts = {row.priority.value: row.count for row in priority_result}
            
            return {
                'status_counts': status_counts,
                'priority_counts': priority_counts,
                'total_jobs': sum(status_counts.values()),
                'pending_jobs': status_counts.get('pending', 0),
                'processing_jobs': status_counts.get('processing', 0)
            }
            
        except Exception as e:
            raise RepositoryError(f"Failed to get queue stats: {str(e)}")

    async def get_jobs_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProcessingJob]:
        """Retrieve jobs within a date range."""
        try:
            conditions = [
                ProcessingJobModel.created_at >= start_date,
                ProcessingJobModel.created_at <= end_date
            ]
            
            if user_id:
                conditions.append(ProcessingJobModel.user_id == user_id)
            
            stmt = (
                select(ProcessingJobModel)
                .where(and_(*conditions))
                .order_by(ProcessingJobModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get jobs by date range: {str(e)}")

    async def get_stalled_jobs(
        self,
        stall_threshold_minutes: int = 30,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProcessingJob]:
        """Retrieve jobs that appear to be stalled."""
        try:
            threshold_time = datetime.utcnow() - timedelta(minutes=stall_threshold_minutes)
            
            stmt = (
                select(ProcessingJobModel)
                .where(
                    and_(
                        ProcessingJobModel.status == JobStatus.PROCESSING,
                        ProcessingJobModel.updated_at < threshold_time
                    )
                )
                .order_by(ProcessingJobModel.updated_at.asc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get stalled jobs: {str(e)}")

    async def get_next_jobs_in_queue(
        self,
        limit: int = 10,
        priority_order: bool = True
    ) -> List[ProcessingJob]:
        """Get next jobs to process from the queue."""
        try:
            stmt = (
                select(ProcessingJobModel)
                .where(ProcessingJobModel.status == JobStatus.PENDING)
            )
            
            if priority_order:
                stmt = stmt.order_by(
                    ProcessingJobModel.priority.desc(),
                    ProcessingJobModel.created_at.asc()
                )
            else:
                stmt = stmt.order_by(ProcessingJobModel.created_at.asc())
            
            stmt = stmt.limit(limit)
            result = await self._session.execute(stmt)
            job_models = result.scalars().all()
            
            return [model.to_domain_entity() for model in job_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to get next jobs in queue: {str(e)}")

    async def update_job_status(self, job_id: UUID, status: JobStatus) -> bool:
        """Update only the status of a job."""
        try:
            stmt = (
                update(ProcessingJobModel)
                .where(ProcessingJobModel.id == job_id)
                .values(status=status, updated_at=datetime.utcnow())
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to update job status: {str(e)}")

    async def update_job_stage(self, job_id: UUID, stage: ProcessingStage) -> bool:
        """Update only the processing stage of a job."""
        try:
            stmt = (
                update(ProcessingJobModel)
                .where(ProcessingJobModel.id == job_id)
                .values(current_stage=stage, updated_at=datetime.utcnow())
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to update job stage: {str(e)}")

    async def update_job_progress(self, job_id: UUID, progress: float) -> bool:
        """Update the progress of a job."""
        try:
            stmt = (
                update(ProcessingJobModel)
                .where(ProcessingJobModel.id == job_id)
                .values(progress=progress, updated_at=datetime.utcnow())
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to update job progress: {str(e)}")

    async def bulk_update_status(
        self,
        job_ids: List[UUID],
        status: JobStatus
    ) -> int:
        """Update status for multiple jobs."""
        try:
            stmt = (
                update(ProcessingJobModel)
                .where(ProcessingJobModel.id.in_(job_ids))
                .values(status=status, updated_at=datetime.utcnow())
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to bulk update job status: {str(e)}")

    async def cleanup_old_jobs(
        self,
        older_than_days: int = 30,
        statuses: Optional[List[JobStatus]] = None
    ) -> int:
        """Clean up old jobs based on age and status."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            
            conditions = [ProcessingJobModel.created_at < cutoff_date]
            
            if statuses:
                conditions.append(ProcessingJobModel.status.in_(statuses))
            
            stmt = delete(ProcessingJobModel).where(and_(*conditions))
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to cleanup old jobs: {str(e)}")