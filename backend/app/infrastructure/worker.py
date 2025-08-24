#!/usr/bin/env python3
"""
Background Worker for SEELE-E Backend

Handles asynchronous processing of credential extraction jobs.
Processes jobs from Redis queue and updates job status in database.
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional
from loguru import logger

from ..core.config.settings import get_settings
from ..infrastructure.database.connection import DatabaseManager
from ..infrastructure.database.session import get_async_db_context
from ..infrastructure.external.ai_providers.factory import AIProviderFactory
from ..domain.entities.processing_job import JobStatus, ProcessingStage
from ..infrastructure.repositories.processing_job_repository_impl import ProcessingJobRepositoryImpl
from ..infrastructure.repositories.credential_repository_impl import CredentialRepositoryImpl


class BackgroundWorker:
    """Background worker for processing credential extraction jobs."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_manager: Optional[DatabaseManager] = None
        self.ai_factory: Optional[AIProviderFactory] = None
        self.job_repository: Optional[ProcessingJobRepositoryImpl] = None
        self.credential_repository: Optional[CredentialRepositoryImpl] = None
        self.running = False
        self.worker_id = f"worker-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
    async def initialize(self) -> None:
        """Initialize worker components."""
        logger.info(f"🔧 Initializing worker {self.worker_id}...")
        
        # Initialize database
        self.db_manager = DatabaseManager()
        await self.db_manager.initialize()
        logger.info("✅ Database initialized")
        
        # Initialize AI providers
        self.ai_factory = AIProviderFactory()
        await self.ai_factory.initialize_providers()
        logger.info("✅ AI providers initialized")
        
        logger.info("✅ Worker components initialized")
        
        logger.info(f"🎉 Worker {self.worker_id} initialized successfully")
    
    async def start(self) -> None:
        """Start the worker main loop."""
        logger.info(f"🚀 Starting worker {self.worker_id}...")
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            while self.running:
                await self._process_pending_jobs()
                await asyncio.sleep(5)  # Check for new jobs every 5 seconds
                
        except Exception as e:
            logger.error(f"❌ Worker error: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _process_pending_jobs(self) -> None:
        """Process pending jobs from the queue."""
        try:
            # Get database session and repositories
            async with get_async_db_context() as session:
                job_repository = ProcessingJobRepositoryImpl(session)
                credential_repository = CredentialRepositoryImpl(session)
                
                # Get pending jobs (limit to 10 at a time)
                pending_jobs = await job_repository.get_pending_jobs(limit=10)
            
            if not pending_jobs:
                return
                
            logger.info(f"📋 Found {len(pending_jobs)} pending jobs")
            
            for job in pending_jobs:
                if not self.running:
                    break
                    
                try:
                    await self._process_job(job, job_repository, credential_repository)
                except Exception as e:
                    logger.error(f"❌ Error processing job {job.id}: {e}")
                    # Mark job as failed
                    job.fail([f"Worker error: {str(e)}"])
                    await job_repository.update(job)
                    
        except Exception as e:
            logger.error(f"❌ Error getting pending jobs: {e}")
    
    async def _process_job(self, job, job_repository, credential_repository) -> None:
        """Process a single job."""
        logger.info(f"🔄 Processing job {job.id} for credential {job.credential_id}")
        
        # Update job status to processing
        job.start_processing(self.worker_id)
        await job_repository.update(job)
        
        try:
            # Get credential
            credential = await credential_repository.get_by_id(job.credential_id)
            if not credential:
                raise Exception(f"Credential {job.credential_id} not found")
            
            # Simulate processing stages
            stages = [
                ProcessingStage.PREPROCESSING,
                ProcessingStage.OCR_EXTRACTION,
                ProcessingStage.QR_EXTRACTION,
                ProcessingStage.AI_PROCESSING,
                ProcessingStage.VALIDATION,
                ProcessingStage.POSTPROCESSING
            ]
            
            for i, stage in enumerate(stages):
                if not self.running:
                    break
                    
                logger.info(f"📊 Job {job.id}: {stage.value}")
                job.update_stage(stage)
                job.update_progress((i + 1) / len(stages) * 100)
                await job_repository.update(job)
                
                # Simulate processing time
                await asyncio.sleep(2)
            
            # Complete job
            job.complete({
                "extracted_data": {
                    "name": "Simulated Name",
                    "id_number": "123456789",
                    "processed_at": datetime.now().isoformat()
                },
                "confidence_score": 0.95,
                "processing_time": 10.0
            })
            
            await job_repository.update(job)
            logger.info(f"✅ Job {job.id} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Job {job.id} failed: {e}")
            job.fail([str(e)])
            await job_repository.update(job)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"🛑 Received signal {signum}, shutting down worker...")
        self.running = False
    
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        logger.info(f"🧹 Cleaning up worker {self.worker_id}...")
        
        try:
            if self.db_manager:
                await self.db_manager.close()
                logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
        
        logger.info(f"👋 Worker {self.worker_id} shutdown complete")


async def main():
    """Main worker entry point."""
    logger.info("🎯 Starting SEELE-E Background Worker...")
    
    worker = BackgroundWorker()
    
    try:
        await worker.initialize()
        await worker.start()
    except KeyboardInterrupt:
        logger.info("🛑 Worker interrupted by user")
    except Exception as e:
        logger.error(f"❌ Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())