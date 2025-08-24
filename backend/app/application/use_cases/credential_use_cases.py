#!/usr/bin/env python3
"""
Credential Use Cases

Implements business logic for credential processing operations including
upload, validation, classification, extraction, and processing workflows.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from io import BytesIO
from PIL import Image

from fastapi import UploadFile, HTTPException

from ..dto.credential_dto import (
    CredentialUploadRequest, CredentialUploadResponse,
    CredentialValidationRequest, CredentialValidationResponse,
    CredentialClassificationRequest, CredentialClassificationResponse,
    CredentialExtractionRequest, CredentialProcessRequest, CredentialProcessResponse,
    OCRExtractionRequest, OCRExtractionResponse,
    QRExtractionRequest, QRExtractionResponse,
    CredentialHistoryResponse, CredentialStatsResponse,
    CredentialRetryRequest, CredentialRetryResponse,
    CredentialResponse
)
from ...domain.entities.credential import Credential, CredentialType, ProcessingStatus, ExtractionMethod
from ...domain.repositories.credential_repository import CredentialRepository
from ...domain.services.credential_service import CredentialService
from ...infrastructure.external.ocr.ocr_factory import OCRServiceFactory
from ...infrastructure.external.ai_providers.factory import get_ai_factory
from ...core.exceptions.base import ValidationException, CredentialProcessingError
from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CredentialUseCases:
    """Use cases for credential processing operations."""
    
    def __init__(
        self,
        credential_repository: CredentialRepository,
        credential_service: CredentialService,
        ocr_factory: OCRServiceFactory
    ):
        self.credential_repository = credential_repository
        self.credential_service = credential_service
        self.ocr_factory = ocr_factory
    
    async def upload_credential(
        self,
        file: UploadFile,
        request: CredentialUploadRequest,
        user_id: UUID
    ) -> CredentialUploadResponse:
        """Upload and queue credential for processing."""
        try:
            logger.info(f"Starting credential upload for user {user_id}")
            
            # Validate file
            await self._validate_upload_file(file)
            
            # Read file content
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Submit credential for processing
            credential, processing_job_id = await self.credential_service.submit_credential_for_processing(
                user_id=user_id,
                file_content=file_content,
                filename=file.filename,
                mime_type=file.content_type,
                credential_type=request.credential_type,
                extraction_method=request.extraction_method,
                extract_qr=request.extract_qr,
                preferred_ai_provider=request.preferred_ai_provider,
                validate_dimensions=request.validate_dimensions
            )
            
            # Convert to response
            credential_response = await self._credential_to_response(credential)
            
            return CredentialUploadResponse(
                credential=credential_response,
                processing_job_id=processing_job_id,
                estimated_processing_time=self._estimate_processing_time(request.extraction_method)
            )
            
        except Exception as e:
            logger.error(f"Error uploading credential: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def validate_credential(
        self,
        file: UploadFile,
        request: CredentialValidationRequest
    ) -> CredentialValidationResponse:
        """Validate credential file without processing."""
        try:
            logger.info(f"Validating credential file: {file.filename}")
            
            validation_errors = []
            
            # Read file content
            file_content = await file.read()
            await file.seek(0)
            
            # Check file format
            if request.check_format:
                if not self._is_supported_format(file.content_type):
                    validation_errors.append(f"Unsupported file format: {file.content_type}")
            
            # Check file size
            file_size = len(file_content)
            if file_size > settings.MAX_FILE_SIZE:
                validation_errors.append(f"File size exceeds maximum allowed: {file_size} > {settings.MAX_FILE_SIZE}")
            
            # Check image dimensions and quality
            image_dimensions = {"width": 0, "height": 0}
            quality_score = 0.0
            
            if request.check_dimensions or request.check_quality:
                try:
                    image = Image.open(BytesIO(file_content))
                    image_dimensions = {"width": image.width, "height": image.height}
                    
                    if request.check_dimensions:
                        if image.width < settings.MIN_IMAGE_WIDTH or image.height < settings.MIN_IMAGE_HEIGHT:
                            validation_errors.append(
                                f"Image dimensions too small: {image.width}x{image.height} < "
                                f"{settings.MIN_IMAGE_WIDTH}x{settings.MIN_IMAGE_HEIGHT}"
                            )
                    
                    if request.check_quality:
                        quality_score = await self._calculate_image_quality(image)
                        if quality_score < 0.5:
                            validation_errors.append(f"Image quality too low: {quality_score:.2f}")
                            
                except Exception as e:
                    validation_errors.append(f"Error processing image: {str(e)}")
            
            is_valid = len(validation_errors) == 0
            message = "Credential is valid" if is_valid else "Credential validation failed"
            
            return CredentialValidationResponse(
                is_valid=is_valid,
                validation_errors=validation_errors,
                image_dimensions=image_dimensions,
                file_size=file_size,
                mime_type=file.content_type,
                quality_score=quality_score,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error validating credential: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def classify_credential(
        self,
        file: UploadFile,
        request: CredentialClassificationRequest
    ) -> CredentialClassificationResponse:
        """Classify credential type from image."""
        try:
            logger.info(f"Classifying credential: {file.filename}")
            
            # Read file content
            file_content = await file.read()
            await file.seek(0)
            
            # Get image processor
            image_processor = self.ocr_factory.get_image_processor()
            
            # Detect credential type
            credential_type, confidence = await image_processor.detect_credential_type(file_content)
            
            # If local detection fails and AI fallback is enabled
            if confidence < 0.7 and request.use_ai_fallback:
                try:
                    ai_factory = await get_ai_factory()
                    if ai_factory.is_initialized():
                        # Use AI for classification
                        ai_result = await ai_factory.process_request(
                            "classify_credential",
                            {"image_data": file_content}
                        )
                        if ai_result and ai_result.get("credential_type"):
                            credential_type = CredentialType(ai_result["credential_type"])
                            confidence = ai_result.get("confidence", confidence)
                except Exception as e:
                    logger.warning(f"AI classification failed: {str(e)}")
            
            # Get alternative types (mock implementation)
            alternative_types = [
                {"type": "tipo1", "confidence": 0.3},
                {"type": "tipo2", "confidence": 0.2}
            ]
            
            detection_method = "ai_hybrid" if request.use_ai_fallback else "local_ocr"
            message = f"Credential classified as {credential_type.value} with {confidence:.2f} confidence"
            
            return CredentialClassificationResponse(
                credential_type=credential_type,
                confidence=confidence,
                detection_method=detection_method,
                alternative_types=alternative_types,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error classifying credential: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def extract_ocr_data(
        self,
        file: UploadFile,
        request: OCRExtractionRequest
    ) -> OCRExtractionResponse:
        """Extract OCR data from credential."""
        try:
            logger.info(f"Extracting OCR data from {request.side} of {request.credential_type.value}")
            
            # Read file content
            file_content = await file.read()
            await file.seek(0)
            
            start_time = datetime.now()
            
            # Get OCR service
            ocr_service = self.ocr_factory.get_ocr_service()
            
            # Extract text
            extracted_text, confidence = await ocr_service.extract_text(
                file_content,
                request.credential_type,
                request.side
            )
            
            # If OCR fails and AI fallback is enabled
            if confidence < 0.5 and request.use_ai_fallback:
                try:
                    ai_factory = await get_ai_factory()
                    if ai_factory.is_initialized():
                        ai_result = await ai_factory.process_request(
                            "extract_text",
                            {
                                "image_data": file_content,
                                "credential_type": request.credential_type.value,
                                "side": request.side
                            }
                        )
                        if ai_result and ai_result.get("text"):
                            extracted_text = ai_result["text"]
                            confidence = ai_result.get("confidence", confidence)
                except Exception as e:
                    logger.warning(f"AI OCR extraction failed: {str(e)}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Parse structured data (mock implementation)
            structured_data = self._parse_ocr_text(extracted_text, request.credential_type)
            
            extraction_method = "ai_hybrid" if request.use_ai_fallback else "tesseract_ocr"
            message = f"OCR extraction completed with {confidence:.2f} confidence"
            
            return OCRExtractionResponse(
                extracted_text=extracted_text,
                confidence=confidence,
                extraction_method=extraction_method,
                processing_time=processing_time,
                structured_data=structured_data,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error extracting OCR data: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def extract_qr_data(
        self,
        file: UploadFile,
        request: QRExtractionRequest
    ) -> QRExtractionResponse:
        """Extract QR code data from credential."""
        try:
            logger.info(f"Extracting QR data from {request.credential_type.value}")
            
            # Read file content
            file_content = await file.read()
            await file.seek(0)
            
            start_time = datetime.now()
            
            # Get QR service
            qr_service = self.ocr_factory.get_qr_service()
            
            # Extract QR data
            qr_data, confidence = await qr_service.extract_qr_data(
                file_content,
                request.credential_type,
                enhanced=request.use_enhanced_detection
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Validate INE QR format
            is_valid_ine_qr = qr_service.validate_ine_qr_data(qr_data) if qr_data else False
            
            extraction_method = "enhanced_detection" if request.use_enhanced_detection else "standard_detection"
            message = f"QR extraction completed with {confidence:.2f} confidence"
            
            return QRExtractionResponse(
                qr_data=qr_data or "",
                is_valid_ine_qr=is_valid_ine_qr,
                confidence=confidence,
                extraction_method=extraction_method,
                processing_time=processing_time,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error extracting QR data: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def process_credential(
        self,
        file: UploadFile,
        request: CredentialProcessRequest,
        user_id: UUID
    ) -> CredentialProcessResponse:
        """Process credential completely (upload + extract + validate)."""
        try:
            logger.info(f"Processing credential for user {user_id}")
            
            # Upload credential first
            upload_request = CredentialUploadRequest(
                credential_type=request.credential_type,
                extract_qr=request.extract_qr,
                preferred_ai_provider=request.preferred_ai_provider,
                extraction_method=request.extraction_method,
                validate_dimensions=request.validate_dimensions
            )
            
            upload_response = await self.upload_credential(file, upload_request, user_id)
            
            # Wait for processing to complete (in real implementation, this would be async)
            await asyncio.sleep(2)  # Simulate processing time
            
            # Get updated credential
            credential = await self.credential_repository.get_by_id(upload_response.credential.id)
            if not credential:
                raise CredentialProcessingError("Credential not found after processing")
            
            credential_response = await self._credential_to_response(credential)
            
            # Create processing summary
            processing_summary = {
                "processing_time": credential.processing_duration or 0.0,
                "extraction_method": credential.extraction_method.value if credential.extraction_method else None,
                "status": credential.processing_status.value,
                "qr_extracted": credential.processing_metrics.qr_detected,
                "confidence_score": credential.processing_metrics.ai_confidence
            }
            
            # Mock cost breakdown
            cost_breakdown = {
                "ocr_cost": 0.01,
                "ai_cost": 0.05 if credential.extraction_method in [ExtractionMethod.OPENAI, ExtractionMethod.DEEPSEEK] else 0.0,
                "total_cost": 0.06
            }
            
            return CredentialProcessResponse(
                credential=credential_response,
                processing_summary=processing_summary,
                cost_breakdown=cost_breakdown
            )
            
        except Exception as e:
            logger.error(f"Error processing credential: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_credential_history(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[ProcessingStatus] = None
    ) -> CredentialHistoryResponse:
        """Get credential processing history for user."""
        try:
            logger.info(f"Getting credential history for user {user_id}")
            
            # Get credentials with pagination
            credentials, total_count = await self.credential_repository.get_by_user_paginated(
                user_id=user_id,
                page=page,
                page_size=page_size,
                status_filter=status_filter
            )
            
            # Convert to responses
            credential_responses = []
            for credential in credentials:
                credential_response = await self._credential_to_response(credential)
                credential_responses.append(credential_response)
            
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_previous = page > 1
            
            return CredentialHistoryResponse(
                credentials=credential_responses,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_next=has_next,
                has_previous=has_previous,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error getting credential history: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_credential_stats(
        self,
        user_id: UUID
    ) -> CredentialStatsResponse:
        """Get credential processing statistics for user."""
        try:
            logger.info(f"Getting credential stats for user {user_id}")
            
            # Get stats from repository
            stats = await self.credential_repository.get_user_stats(user_id)
            
            return CredentialStatsResponse(
                total_processed=stats.get("total_processed", 0),
                successful_extractions=stats.get("successful_extractions", 0),
                failed_extractions=stats.get("failed_extractions", 0),
                average_processing_time=stats.get("average_processing_time", 0.0),
                by_credential_type=stats.get("by_credential_type", {}),
                by_extraction_method=stats.get("by_extraction_method", {}),
                by_status=stats.get("by_status", {}),
                cost_summary=stats.get("cost_summary", {})
            )
            
        except Exception as e:
            logger.error(f"Error getting credential stats: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def retry_credential(
        self,
        credential_id: UUID,
        request: CredentialRetryRequest,
        user_id: UUID
    ) -> CredentialRetryResponse:
        """Retry processing failed credential."""
        try:
            logger.info(f"Retrying credential {credential_id} for user {user_id}")
            
            # Get credential
            credential = await self.credential_repository.get_by_id(credential_id)
            if not credential or credential.user_id != user_id:
                raise HTTPException(status_code=404, detail="Credential not found")
            
            # Retry processing
            processing_job_id = await self.credential_service.retry_failed_credential(
                credential_id=credential_id,
                extraction_method=request.extraction_method,
                preferred_ai_provider=request.preferred_ai_provider
            )
            
            return CredentialRetryResponse(
                processing_job_id=processing_job_id,
                estimated_processing_time=self._estimate_processing_time(request.extraction_method)
            )
            
        except Exception as e:
            logger.error(f"Error retrying credential: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_credential(
        self,
        credential_id: UUID,
        user_id: UUID
    ) -> CredentialResponse:
        """Get specific credential by ID."""
        try:
            logger.info(f"Getting credential {credential_id} for user {user_id}")
            
            credential = await self.credential_repository.get_by_id(credential_id)
            if not credential or credential.user_id != user_id:
                raise HTTPException(status_code=404, detail="Credential not found")
            
            return await self._credential_to_response(credential)
            
        except Exception as e:
            logger.error(f"Error getting credential: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    # Helper methods
    
    async def _validate_upload_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        if not file.filename:
            raise ValidationException("Filename is required")
        
        if not self._is_supported_format(file.content_type):
            raise ValidationException(f"Unsupported file format: {file.content_type}")
        
        # Check file size
        file_content = await file.read()
        await file.seek(0)
        
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise ValidationException(f"File size exceeds maximum allowed: {len(file_content)} > {settings.MAX_FILE_SIZE}")
    
    def _is_supported_format(self, mime_type: str) -> bool:
        """Check if file format is supported."""
        supported_formats = [
            "image/jpeg", "image/jpg", "image/png", "image/bmp", "image/tiff"
        ]
        return mime_type in supported_formats
    
    async def _calculate_image_quality(self, image: Image.Image) -> float:
        """Calculate image quality score."""
        # Mock implementation - in real scenario, analyze sharpness, contrast, etc.
        return 0.85
    
    def _parse_ocr_text(self, text: str, credential_type: CredentialType) -> Dict[str, Any]:
        """Parse OCR text into structured data."""
        # Mock implementation - in real scenario, use regex patterns for each credential type
        return {
            "raw_text": text,
            "parsed_fields": {},
            "confidence": 0.8
        }
    
    def _estimate_processing_time(self, extraction_method: ExtractionMethod) -> int:
        """Estimate processing time based on extraction method."""
        time_estimates = {
            ExtractionMethod.OCR_ONLY: 5,
            ExtractionMethod.QR_ONLY: 3,
            ExtractionMethod.HYBRID: 8,
            ExtractionMethod.OPENAI: 15,
            ExtractionMethod.DEEPSEEK: 12,
            ExtractionMethod.GEMINI: 10,
            ExtractionMethod.CLAUDE: 13
        }
        return time_estimates.get(extraction_method, 10)
    
    async def _credential_to_response(self, credential: Credential) -> CredentialResponse:
        """Convert credential entity to response DTO."""
        from ..dto.credential_dto import PersonalInfoResponse, ProcessingMetricsResponse, QualityScoreResponse
        
        # Convert personal info
        personal_info = None
        if credential.personal_info:
            personal_info = PersonalInfoResponse(
                nombre=credential.personal_info.nombre,
                apellido_paterno=credential.personal_info.apellido_paterno,
                apellido_materno=credential.personal_info.apellido_materno,
                curp=credential.personal_info.curp,
                fecha_nacimiento=credential.personal_info.fecha_nacimiento,
                sexo=credential.personal_info.sexo,
                domicilio=credential.personal_info.domicilio,
                clave_elector=credential.personal_info.clave_elector,
                seccion=credential.personal_info.seccion,
                localidad=credential.personal_info.localidad,
                municipio=credential.personal_info.municipio,
                estado=credential.personal_info.estado,
                vigencia=credential.personal_info.vigencia,
                emision=credential.personal_info.emision
            )
        
        # Convert processing metrics
        processing_metrics = ProcessingMetricsResponse(
            ocr_confidence=credential.processing_metrics.ocr_confidence,
            qr_detected=credential.processing_metrics.qr_detected,
            qr_confidence=credential.processing_metrics.qr_confidence,
            ai_confidence=credential.processing_metrics.ai_confidence,
            processing_time=credential.processing_metrics.processing_time,
            retry_count=credential.processing_metrics.retry_count,
            validation_score=credential.processing_metrics.validation_score
        )
        
        # Convert quality score
        quality_score = None
        if credential.quality_score:
            quality_score = QualityScoreResponse(
                overall_score=credential.quality_score.overall_score,
                ocr_quality=credential.quality_score.ocr_quality,
                data_completeness=credential.quality_score.data_completeness,
                confidence_score=credential.quality_score.confidence_score
            )
        
        return CredentialResponse(
            id=credential.id,
            user_id=credential.user_id,
            credential_type=credential.credential_type,
            processing_status=credential.processing_status,
            extraction_method=credential.extraction_method,
            original_filename=credential.original_filename,
            file_size=credential.file_size,
            file_hash=credential.file_hash,
            mime_type=credential.mime_type,
            processing_started_at=credential.processing_started_at,
            processing_completed_at=credential.processing_completed_at,
            processing_duration=credential.processing_duration,
            personal_info=personal_info,
            processing_metrics=processing_metrics,
            quality_score=quality_score,
            error_message=credential.error_message,
            error_code=credential.error_code,
            processing_logs=credential.processing_logs,
            is_valid=credential.is_valid,
            validation_errors=credential.validation_errors,
            created_at=credential.created_at,
            updated_at=credential.updated_at
        )