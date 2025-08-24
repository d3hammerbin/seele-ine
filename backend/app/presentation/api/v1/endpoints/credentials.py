#!/usr/bin/env python3
"""
Credential API Endpoints

REST API endpoints for INE credential processing operations including
upload, validation, classification, extraction, and processing workflows.
"""

import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from .....application.dto.credential_dto import (
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
from .....application.use_cases.credential_use_cases import CredentialUseCases
from .....domain.entities.credential import ProcessingStatus, CredentialType, ExtractionMethod
from .....domain.entities.user import User
from .....infrastructure.repositories.credential_repository_impl import CredentialRepositoryImpl
from .....domain.services.credential_service import CredentialService
from .....infrastructure.external.ocr.ocr_factory import OCRServiceFactory
from .....core.security.dependencies import get_current_user, get_api_key_user
from .....infrastructure.database.session import get_async_db_session
from .....core.exceptions.handlers import handle_api_error
from .....core.rate_limiting.dependencies import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credentials", tags=["credentials"])


# Dependency to get credential use cases
async def get_credential_use_cases(
    db: AsyncSession = Depends(get_async_db_session)
) -> CredentialUseCases:
    """Get credential use cases with dependencies."""
    credential_repository = CredentialRepositoryImpl(db)
    credential_service = CredentialService(credential_repository)
    ocr_factory = OCRServiceFactory()
    
    return CredentialUseCases(
        credential_repository=credential_repository,
        credential_service=credential_service,
        ocr_factory=ocr_factory
    )


@router.post(
    "/upload",
    response_model=CredentialUploadResponse,
    summary="Upload credential for processing",
    description="Upload an INE credential image file and queue it for processing. Supports automatic type detection and various extraction methods.",
    responses={
        200: {"description": "Credential uploaded successfully"},
        400: {"description": "Invalid file or request parameters"},
        401: {"description": "Authentication required"},
        413: {"description": "File too large"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=10, window=60)  # 10 requests per minute
async def upload_credential(
    file: UploadFile = File(..., description="INE credential image file"),
    credential_type: Optional[CredentialType] = Query(None, description="Credential type (auto-detected if not provided)"),
    extract_qr: bool = Query(True, description="Whether to extract QR code data"),
    preferred_ai_provider: Optional[str] = Query(None, description="Preferred AI provider (openai, deepseek, gemini, claude)"),
    extraction_method: ExtractionMethod = Query(ExtractionMethod.HYBRID, description="Extraction method to use"),
    validate_dimensions: bool = Query(True, description="Whether to validate image dimensions"),
    current_user: User = Depends(get_current_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Upload credential for processing."""
    try:
        request = CredentialUploadRequest(
            credential_type=credential_type,
            extract_qr=extract_qr,
            preferred_ai_provider=preferred_ai_provider,
            extraction_method=extraction_method,
            validate_dimensions=validate_dimensions
        )
        
        result = await use_cases.upload_credential(file, request, current_user.id)
        return result
        
    except Exception as e:
        return await handle_api_error(e, "upload_credential")


@router.post(
    "/validate",
    response_model=CredentialValidationResponse,
    summary="Validate credential file",
    description="Validate an INE credential image file without processing it. Checks format, dimensions, and quality.",
    responses={
        200: {"description": "Validation completed"},
        400: {"description": "Invalid file or request parameters"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=20, window=60)  # 20 requests per minute
async def validate_credential(
    file: UploadFile = File(..., description="INE credential image file"),
    check_dimensions: bool = Query(True, description="Check image dimensions"),
    check_format: bool = Query(True, description="Check file format"),
    check_quality: bool = Query(True, description="Check image quality"),
    current_user: User = Depends(get_current_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Validate credential file."""
    try:
        request = CredentialValidationRequest(
            check_dimensions=check_dimensions,
            check_format=check_format,
            check_quality=check_quality
        )
        
        result = await use_cases.validate_credential(file, request)
        return result
        
    except Exception as e:
        return await handle_api_error(e, "validate_credential")


@router.post(
    "/classify",
    response_model=CredentialClassificationResponse,
    summary="Classify credential type",
    description="Classify the type of INE credential from an image. Uses local detection with optional AI fallback.",
    responses={
        200: {"description": "Classification completed"},
        400: {"description": "Invalid file or request parameters"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=15, window=60)  # 15 requests per minute
async def classify_credential(
    file: UploadFile = File(..., description="INE credential image file"),
    use_ai_fallback: bool = Query(True, description="Use AI providers if local classification fails"),
    current_user: User = Depends(get_current_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Classify credential type."""
    try:
        request = CredentialClassificationRequest(
            use_ai_fallback=use_ai_fallback
        )
        
        result = await use_cases.classify_credential(file, request)
        return result
        
    except Exception as e:
        return await handle_api_error(e, "classify_credential")


@router.post(
    "/extract/ocr",
    response_model=OCRExtractionResponse,
    summary="Extract OCR data",
    description="Extract text data from INE credential using OCR with optional AI fallback.",
    responses={
        200: {"description": "OCR extraction completed"},
        400: {"description": "Invalid file or request parameters"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=10, window=60)  # 10 requests per minute
async def extract_ocr_data(
    file: UploadFile = File(..., description="INE credential image file"),
    side: str = Query(..., pattern="^(front|back)$", description="Side of credential (front/back)"),
    credential_type: CredentialType = Query(..., description="Type of credential"),
    use_ai_fallback: bool = Query(True, description="Use AI providers if OCR fails"),
    current_user: User = Depends(get_current_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Extract OCR data from credential."""
    try:
        request = OCRExtractionRequest(
            side=side,
            credential_type=credential_type,
            use_ai_fallback=use_ai_fallback
        )
        
        result = await use_cases.extract_ocr_data(file, request)
        return result
        
    except Exception as e:
        return await handle_api_error(e, "extract_ocr_data")


@router.post(
    "/extract/qr",
    response_model=QRExtractionResponse,
    summary="Extract QR code data",
    description="Extract QR code data from INE credential with validation.",
    responses={
        200: {"description": "QR extraction completed"},
        400: {"description": "Invalid file or request parameters"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=15, window=60)  # 15 requests per minute
async def extract_qr_data(
    file: UploadFile = File(..., description="INE credential image file"),
    credential_type: CredentialType = Query(..., description="Type of credential"),
    use_enhanced_detection: bool = Query(True, description="Use enhanced QR detection algorithms"),
    current_user: User = Depends(get_current_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Extract QR code data from credential."""
    try:
        request = QRExtractionRequest(
            credential_type=credential_type,
            use_enhanced_detection=use_enhanced_detection
        )
        
        result = await use_cases.extract_qr_data(file, request)
        return result
        
    except Exception as e:
        return await handle_api_error(e, "extract_qr_data")


@router.post(
    "/process",
    response_model=CredentialProcessResponse,
    summary="Process credential completely",
    description="Complete credential processing including upload, classification, extraction, and validation.",
    responses={
        200: {"description": "Credential processed successfully"},
        400: {"description": "Invalid file or request parameters"},
        401: {"description": "Authentication required"},
        413: {"description": "File too large"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=5, window=60)  # 5 requests per minute (more intensive operation)
async def process_credential(
    file: UploadFile = File(..., description="INE credential image file"),
    credential_type: Optional[CredentialType] = Query(None, description="Credential type (auto-detected if not provided)"),
    extract_qr: bool = Query(True, description="Whether to extract QR code data"),
    validate_dimensions: bool = Query(True, description="Whether to validate image dimensions"),
    preferred_ai_provider: Optional[str] = Query(None, description="Preferred AI provider"),
    extraction_method: ExtractionMethod = Query(ExtractionMethod.HYBRID, description="Extraction method to use"),
    current_user: User = Depends(get_current_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Process credential completely."""
    try:
        request = CredentialProcessRequest(
            credential_type=credential_type,
            extract_qr=extract_qr,
            validate_dimensions=validate_dimensions,
            preferred_ai_provider=preferred_ai_provider,
            extraction_method=extraction_method
        )
        
        result = await use_cases.process_credential(file, request, current_user.id)
        return result
        
    except Exception as e:
        return await handle_api_error(e, "process_credential")


@router.get(
    "/history",
    response_model=CredentialHistoryResponse,
    summary="Get credential processing history",
    description="Get paginated list of processed credentials for the current user.",
    responses={
        200: {"description": "History retrieved successfully"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=30, window=60)  # 30 requests per minute
async def get_credential_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[ProcessingStatus] = Query(None, description="Filter by processing status"),
    current_user: User = Depends(get_current_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Get credential processing history."""
    try:
        result = await use_cases.get_credential_history(
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            status_filter=status_filter
        )
        return result
        
    except Exception as e:
        return await handle_api_error(e, "get_credential_history")


@router.get(
    "/stats",
    response_model=CredentialStatsResponse,
    summary="Get credential processing statistics",
    description="Get processing statistics and metrics for the current user.",
    responses={
        200: {"description": "Statistics retrieved successfully"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=20, window=60)  # 20 requests per minute
async def get_credential_stats(
    current_user: User = Depends(get_current_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Get credential processing statistics."""
    try:
        result = await use_cases.get_credential_stats(current_user.id)
        return result
        
    except Exception as e:
        return await handle_api_error(e, "get_credential_stats")


@router.get(
    "/{credential_id}",
    response_model=CredentialResponse,
    summary="Get specific credential",
    description="Get detailed information about a specific credential by ID.",
    responses={
        200: {"description": "Credential retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Credential not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=50, window=60)  # 50 requests per minute
async def get_credential(
    credential_id: UUID = Path(..., description="Credential ID"),
    current_user: User = Depends(get_current_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Get specific credential by ID."""
    try:
        result = await use_cases.get_credential(credential_id, current_user.id)
        return result
        
    except Exception as e:
        return await handle_api_error(e, "get_credential")


@router.post(
    "/{credential_id}/retry",
    response_model=CredentialRetryResponse,
    summary="Retry failed credential processing",
    description="Retry processing a failed credential with optional new parameters.",
    responses={
        200: {"description": "Credential queued for retry"},
        401: {"description": "Authentication required"},
        404: {"description": "Credential not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=5, window=60)  # 5 requests per minute
async def retry_credential(
    credential_id: UUID = Path(..., description="Credential ID"),
    extraction_method: Optional[ExtractionMethod] = Query(None, description="New extraction method to try"),
    preferred_ai_provider: Optional[str] = Query(None, description="Preferred AI provider for retry"),
    current_user: User = Depends(get_current_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Retry failed credential processing."""
    try:
        request = CredentialRetryRequest(
            extraction_method=extraction_method,
            preferred_ai_provider=preferred_ai_provider
        )
        
        result = await use_cases.retry_credential(credential_id, request, current_user.id)
        return result
        
    except Exception as e:
        return await handle_api_error(e, "retry_credential")


# API Key endpoints (for external integrations)

@router.post(
    "/api-key/upload",
    response_model=CredentialUploadResponse,
    summary="Upload credential via API key",
    description="Upload credential using API key authentication (for external integrations).",
    responses={
        200: {"description": "Credential uploaded successfully"},
        400: {"description": "Invalid file or request parameters"},
        401: {"description": "Invalid API key"},
        413: {"description": "File too large"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=20, window=60)  # 20 requests per minute for API key users
async def upload_credential_api_key(
    file: UploadFile = File(..., description="INE credential image file"),
    credential_type: Optional[CredentialType] = Query(None, description="Credential type"),
    extract_qr: bool = Query(True, description="Whether to extract QR code data"),
    preferred_ai_provider: Optional[str] = Query(None, description="Preferred AI provider"),
    extraction_method: ExtractionMethod = Query(ExtractionMethod.HYBRID, description="Extraction method"),
    validate_dimensions: bool = Query(True, description="Whether to validate image dimensions"),
    api_key_user: User = Depends(get_api_key_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Upload credential via API key."""
    try:
        request = CredentialUploadRequest(
            credential_type=credential_type,
            extract_qr=extract_qr,
            preferred_ai_provider=preferred_ai_provider,
            extraction_method=extraction_method,
            validate_dimensions=validate_dimensions
        )
        
        result = await use_cases.upload_credential(file, request, api_key_user.id)
        return result
        
    except Exception as e:
        return await handle_api_error(e, "upload_credential_api_key")


@router.post(
    "/api-key/process",
    response_model=CredentialProcessResponse,
    summary="Process credential via API key",
    description="Complete credential processing using API key authentication.",
    responses={
        200: {"description": "Credential processed successfully"},
        400: {"description": "Invalid file or request parameters"},
        401: {"description": "Invalid API key"},
        413: {"description": "File too large"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(requests=10, window=60)  # 10 requests per minute for API key users
async def process_credential_api_key(
    file: UploadFile = File(..., description="INE credential image file"),
    credential_type: Optional[CredentialType] = Query(None, description="Credential type"),
    extract_qr: bool = Query(True, description="Whether to extract QR code data"),
    validate_dimensions: bool = Query(True, description="Whether to validate image dimensions"),
    preferred_ai_provider: Optional[str] = Query(None, description="Preferred AI provider"),
    extraction_method: ExtractionMethod = Query(ExtractionMethod.HYBRID, description="Extraction method"),
    api_key_user: User = Depends(get_api_key_user),
    use_cases: CredentialUseCases = Depends(get_credential_use_cases)
):
    """Process credential via API key."""
    try:
        request = CredentialProcessRequest(
            credential_type=credential_type,
            extract_qr=extract_qr,
            validate_dimensions=validate_dimensions,
            preferred_ai_provider=preferred_ai_provider,
            extraction_method=extraction_method
        )
        
        result = await use_cases.process_credential(file, request, api_key_user.id)
        return result
        
    except Exception as e:
        return await handle_api_error(e, "process_credential_api_key")


# Health check endpoint for credentials service
@router.get(
    "/health",
    summary="Credential service health check",
    description="Check the health status of credential processing services.",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def credential_health_check():
    """Health check for credential processing services."""
    try:
        # Check OCR factory
        ocr_factory = OCRFactory()
        ocr_healthy = await ocr_factory.health_check()
        
        # Check AI providers
        from ....infrastructure.external.ai_providers.factory import get_ai_factory
        ai_factory = await get_ai_factory()
        ai_healthy = await ai_factory.health_check() if ai_factory.is_initialized() else False
        
        health_status = {
            "status": "healthy" if ocr_healthy and ai_healthy else "degraded",
            "services": {
                "ocr": "healthy" if ocr_healthy else "unhealthy",
                "ai_providers": "healthy" if ai_healthy else "unhealthy"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        status_code = 200 if ocr_healthy and ai_healthy else 503
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=503
        )