#!/usr/bin/env python3
"""
Scheduler for SEELE-E Backend

Handles scheduled tasks like cleanup, maintenance, and periodic jobs.
Runs background tasks on a schedule using asyncio.
"""

import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from ..core.config.settings import get_settings
from ..infrastructure.database.connection import DatabaseManager
from ..infrastructure.database.session import get_async_db_context
from ..infrastructure.repositories.processing_job_repository_impl import ProcessingJobRepositoryImpl
from ..infrastructure.repositories.credential_repository_impl import CredentialRepositoryImpl
from ..domain.entities.processing_job import JobStatus


class TaskScheduler:
    """Scheduler for periodic background tasks."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_manager: Optional[DatabaseManager] = None
        self.running = False
        self.scheduler_id = f"scheduler-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
    async def initialize(self) -> None:
        """Initialize scheduler components."""
        logger.info(f"🔧 Initializing scheduler {self.scheduler_id}...")
        
        # Initialize database
        self.db_manager = DatabaseManager()
        await self.db_manager.initialize()
        logger.info("✅ Database initialized")
        
        logger.info(f"🎉 Scheduler {self.scheduler_id} initialized successfully")
    
    async def start(self) -> None:
        """Start the scheduler main loop."""
        logger.info(f"🚀 Starting scheduler {self.scheduler_id}...")
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Schedule tasks to run at different intervals
            tasks = [
                self._run_periodic_task(self._cleanup_old_jobs, 3600),  # Every hour
                self._run_periodic_task(self._cleanup_failed_jobs, 1800),  # Every 30 minutes
                self._run_periodic_task(self._update_job_statistics, 300),  # Every 5 minutes
                self._run_periodic_task(self._health_check, 60),  # Every minute
            ]
            
            await asyncio.gather(*tasks)
                
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _run_periodic_task(self, task_func, interval_seconds: int):
        """Run a task periodically at the specified interval."""
        while self.running:
            try:
                await task_func()
            except Exception as e:
                logger.error(f"❌ Error in scheduled task {task_func.__name__}: {e}")
            
            # Wait for the next execution
            await asyncio.sleep(interval_seconds)
    
    async def _cleanup_old_jobs(self) -> None:
        """Clean up old completed jobs."""
        try:
            async with get_async_db_context() as session:
                job_repository = ProcessingJobRepositoryImpl(session)
                
                # Delete jobs older than 30 days
                cutoff_date = datetime.now() - timedelta(days=30)
                
                # Get old completed jobs
                old_jobs = await job_repository.get_by_period(
                    start_date=datetime.min,
                    end_date=cutoff_date
                )
                
                completed_jobs = [job for job in old_jobs if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]]
                
                if completed_jobs:
                    logger.info(f"🧹 Cleaning up {len(completed_jobs)} old jobs")
                    
                    for job in completed_jobs:
                        await job_repository.delete(job.id)
                    
                    logger.info(f"✅ Cleaned up {len(completed_jobs)} old jobs")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up old jobs: {e}")
    
    async def _cleanup_failed_jobs(self) -> None:
        """Clean up failed jobs that are older than 7 days."""
        try:
            async with get_async_db_context() as session:
                job_repository = ProcessingJobRepositoryImpl(session)
                
                # Get failed jobs older than 7 days
                cutoff_date = datetime.now() - timedelta(days=7)
                failed_jobs = await job_repository.get_failed_jobs(limit=100)
                
                old_failed_jobs = [
                    job for job in failed_jobs 
                    if job.failed_at and job.failed_at < cutoff_date
                ]
                
                if old_failed_jobs:
                    logger.info(f"🧹 Cleaning up {len(old_failed_jobs)} old failed jobs")
                    
                    for job in old_failed_jobs:
                        await job_repository.delete(job.id)
                    
                    logger.info(f"✅ Cleaned up {len(old_failed_jobs)} old failed jobs")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up failed jobs: {e}")
    
    async def _update_job_statistics(self) -> None:
        """Update job statistics and metrics."""
        try:
            async with get_async_db_context() as session:
                job_repository = ProcessingJobRepositoryImpl(session)
                
                # Get statistics for the last 24 hours
                start_date = datetime.now() - timedelta(hours=24)
                end_date = datetime.now()
                
                stats = await job_repository.get_job_statistics(
                    period_start=start_date,
                    period_end=end_date
                )
                
                logger.info(f"📊 Job statistics (24h): {stats}")
                
        except Exception as e:
            logger.error(f"❌ Error updating job statistics: {e}")
    
    async def _health_check(self) -> None:
        """Perform health checks on the system."""
        try:
            async with get_async_db_context() as session:
                job_repository = ProcessingJobRepositoryImpl(session)
                
                # Check for stuck jobs (processing for more than 1 hour)
                cutoff_time = datetime.now() - timedelta(hours=1)
                active_jobs = await job_repository.get_active_jobs()
                
                stuck_jobs = [
                    job for job in active_jobs 
                    if job.started_at and job.started_at < cutoff_time and job.status == JobStatus.PROCESSING
                ]
                
                if stuck_jobs:
                    logger.warning(f"⚠️ Found {len(stuck_jobs)} potentially stuck jobs")
                    
                    for job in stuck_jobs:
                        logger.warning(f"⚠️ Stuck job: {job.id} (started: {job.started_at})")
                        # Optionally, you could mark these jobs as failed or retry them
                
        except Exception as e:
            logger.error(f"❌ Error during health check: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"🛑 Received signal {signum}, shutting down scheduler...")
        self.running = False
    
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        logger.info(f"🧹 Cleaning up scheduler {self.scheduler_id}...")
        
        try:
            if self.db_manager:
                await self.db_manager.close()
                logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
        
        logger.info(f"👋 Scheduler {self.scheduler_id} shutdown complete")


async def main():
    """Main scheduler entry point."""
    logger.info("🎯 Starting SEELE-E Task Scheduler...")
    
    scheduler = TaskScheduler()
    
    try:
        await scheduler.initialize()
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler interrupted by user")
    except Exception as e:
        logger.error(f"❌ Scheduler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())